"""
Skill Distillation Module (distill.py)
======================================

Implements the "Hermes-style deep evolution" capability for Primintel.

Core concept:
  After an agent completes a complex task (multi-tool execution), this module
  analyzes the conversation trajectory and uses the LLM to reflect on whether
  the task represents a reusable, generalizable workflow. If yes, it
  automatically generates a new SKILL.md and saves it to the workspace's
  custom skills directory. The SkillManager then picks it up on the next
  refresh, giving the agent "memory" of learned workflows.

Design principles:
  - Silent learning: runs in the background, never interrupts the user.
  - Cost-aware: only triggers when a meaningful number of tool calls are made.
  - Non-blocking: executed in a daemon thread after the user gets their answer.
  - Idempotency: uses a content hash to prevent duplicate skill generation.
"""

import json
import os
import re
import hashlib
import threading
from typing import List, Optional

from common.log import logger


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Max length of conversation history (chars) sent to the reflection LLM
MAX_TRAJECTORY_CHARS = 12000

# Name prefix for auto-generated skills so they are easy to identify
AUTO_SKILL_PREFIX = "auto-"

# Subdirectory inside workspace where distilled skills are stored
SKILLS_SUBDIR = "skills"


def _get_min_tool_calls() -> int:
    """Read distillation_min_tools from config at call time (hot-reloadable)."""
    try:
        from config import conf
        return int(conf().get("distillation_min_tools", 2))
    except Exception:
        return 2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_trajectory(messages: list) -> bool:
    """
    Determine whether the recent conversation trajectory is worth distilling.

    A trajectory is considered "complex enough" to justify distillation when:
    1. The last assistant turn contained at least distillation_min_tools
       unique tool invocations (configurable, default 2).
    2. The conversation has a clear user intent that produced a verifiable result.

    Args:
        messages: Full conversation message list (role/content dicts).

    Returns:
        True if distillation should be attempted, False otherwise.
    """
    if not messages:
        return False

    min_tools = _get_min_tool_calls()
    tool_names = _extract_tool_names_from_last_turn(messages)
    if len(tool_names) < min_tools:
        logger.debug(
            f"[Distill] Skipping: only {len(tool_names)} tool call(s) found "
            f"(min={min_tools})"
        )
        return False

    logger.debug(f"[Distill] Trajectory qualifies for distillation. Tools: {tool_names}")
    return True


def distill_skill_async(messages: list, model, workspace_dir: str) -> None:
    """
    Launch skill distillation in a background daemon thread.

    This is the primary entry point called from the agent loop. It is safe to
    call immediately after the agent completes a turn; the user will never
    wait for it.

    Args:
        messages:      Full conversation history.
        model:         The LLMModel instance to use for reflection.
        workspace_dir: Agent workspace directory (e.g. ~/cow or workspace/).
    """
    if not evaluate_trajectory(messages):
        return

    skills_dir = _resolve_skills_dir(workspace_dir)
    if not skills_dir:
        return

    # Snapshot only the data we need before handing off to the thread
    trajectory_snapshot = _build_trajectory_snapshot(messages)

    thread = threading.Thread(
        target=_distill_in_background,
        args=(trajectory_snapshot, model, skills_dir),
        daemon=True,
        name="skill-distill",
    )
    thread.start()
    logger.debug("[Distill] Background distillation thread started.")


def distill_skill_sync(messages: list, model, workspace_dir: str) -> Optional[str]:
    """
    Synchronous version of skill distillation (useful for CLI / testing).

    Returns the path of the newly created skill directory, or None on failure.
    """
    if not evaluate_trajectory(messages):
        return None

    skills_dir = _resolve_skills_dir(workspace_dir)
    if not skills_dir:
        return None

    trajectory_snapshot = _build_trajectory_snapshot(messages)
    return _distill_in_background(trajectory_snapshot, model, skills_dir)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_tool_names_from_last_turn(messages: list) -> List[str]:
    """
    Scan backwards through messages to find all unique tool names called
    during the most recent assistant turn.
    """
    tool_names: List[str] = []
    in_last_assistant_turn = False

    for msg in reversed(messages):
        role = msg.get("role", "")
        content = msg.get("content", [])

        if role == "assistant":
            in_last_assistant_turn = True
            # Content may be a list of typed blocks
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "")
                        if name and name not in tool_names:
                            tool_names.append(name)
            continue

        # Once we reach a user message after scanning the assistant, stop
        if in_last_assistant_turn and role == "user":
            break

    return tool_names


def _build_trajectory_snapshot(messages: list) -> str:
    """
    Build a compact text representation of the conversation suitable for
    feeding to the reflection LLM. Keeps only the last few turns and
    truncates long tool results to save tokens.
    """
    lines: List[str] = []
    # Take the last 20 messages at most
    recent = messages[-20:]

    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if isinstance(content, str):
            lines.append(f"[{role.upper()}]: {content[:800]}")
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")
                if btype == "text":
                    lines.append(f"[{role.upper()}]: {block.get('text', '')[:800]}")
                elif btype == "tool_use":
                    name = block.get("name", "tool")
                    args = json.dumps(block.get("input", {}), ensure_ascii=False)[:400]
                    lines.append(f"[TOOL_CALL] {name}({args})")
                elif btype == "tool_result":
                    result_text = ""
                    rc = block.get("content", "")
                    if isinstance(rc, list):
                        for rb in rc:
                            if isinstance(rb, dict) and rb.get("type") == "text":
                                result_text += rb.get("text", "")
                    else:
                        result_text = str(rc)
                    lines.append(f"[TOOL_RESULT]: {result_text[:600]}")

    snapshot = "\n".join(lines)
    # Hard cap to avoid huge prompts
    if len(snapshot) > MAX_TRAJECTORY_CHARS:
        snapshot = snapshot[-MAX_TRAJECTORY_CHARS:]
    return snapshot


def _build_reflection_prompt(trajectory: str) -> str:
    """
    Build the metaprompt sent to the LLM for skill generation.

    The prompt instructs the LLM to:
    1. Identify if the trajectory represents a reusable workflow.
    2. If yes, produce a complete SKILL.md in the correct format.
    3. If no, output an empty JSON object so we can detect and skip it.
    """
    return f"""You are a skill-extraction specialist for an AI agent system.

Analyze the following conversation trajectory between a user and an AI agent:

<trajectory>
{trajectory}
</trajectory>

Your job:
1. Determine if the agent followed a **generalizable, reusable workflow** that other users might want to repeat.
   - Reusable: yes if the workflow is a clear multi-step process applicable to more than one user
   - Reusable: NO if it was a one-off creative task, a simple single-step lookup, or highly personal content

2. If reusable, generate a compact SKILL.md file for this workflow following the EXACT format below.
   If not reusable, output exactly: {{"skill": null}}

SKILL.md FORMAT (output only the raw markdown, nothing else, inside the JSON field "skill"):

---
name: <hyphen-case-name-under-50-chars>
description: <one or two sentences: what the skill does AND the exact trigger scenarios. Start with a verb. Be specific.>
metadata:
  always: false
---

# <Title>

## Overview
<2–3 sentence description of the workflow>

## When to Use
<Explicit list of trigger scenarios: "Use when the user asks to...">

## Step-by-Step Workflow
<Numbered list of the precise steps the agent should follow, referencing tools by name>

## Example Invocation
<Short example of a user message that should trigger this skill>

OUTPUT FORMAT — respond ONLY with valid JSON:
{{"skill": "<full SKILL.md content as a JSON string, or null>"}}
"""


def _call_llm_for_reflection(prompt: str, model) -> Optional[str]:
    """
    Call the LLM with the reflection prompt and parse the SKILL.md out of
    the response.

    Returns the raw SKILL.md string, or None if not applicable / on error.
    """
    try:
        # Use a simple synchronous call if available, otherwise fall back
        if hasattr(model, "reply_text"):
            response = model.reply_text(prompt)
        elif hasattr(model, "chat"):
            from agent.protocol.models import LLMRequest
            req = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                system="You are a concise skill extraction assistant. Output only valid JSON.",
                max_tokens=1500,
            )
            response = model.chat(req)
        else:
            logger.warning("[Distill] Model has no usable text generation method.")
            return None
    except Exception as e:
        logger.warning(f"[Distill] LLM call failed: {e}")
        return None

    if not response:
        return None

    # Extract JSON from the response
    try:
        # Strip markdown code blocks if present
        clean = re.sub(r"```(?:json)?\s*", "", response).strip().rstrip("```").strip()
        # Find the JSON object
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if not match:
            logger.debug("[Distill] No JSON found in LLM response.")
            return None
        data = json.loads(match.group(0))
        skill_content = data.get("skill")
        if not skill_content or skill_content == "null":
            logger.debug("[Distill] LLM determined workflow is not reusable.")
            return None
        return skill_content
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logger.warning(f"[Distill] Failed to parse LLM JSON response: {e}")
        logger.debug(f"[Distill] Raw response was: {response[:500]}")
        return None


def _extract_skill_name(skill_content: str) -> Optional[str]:
    """
    Parse the skill name from the SKILL.md frontmatter.
    Returns None if unparseable.
    """
    match = re.search(r'^name:\s*(.+)$', skill_content, re.MULTILINE)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        # Sanitize: keep only lowercase alphanumeric and hyphens
        name = re.sub(r'[^a-z0-9\-]', '-', name.lower())
        name = re.sub(r'-+', '-', name).strip('-')
        return name[:64]
    return None


def _compute_content_hash(skill_content: str) -> str:
    """Compute a short hash of the skill body for deduplication."""
    return hashlib.sha1(skill_content.encode("utf-8")).hexdigest()[:8]


def _save_skill(skill_content: str, skills_dir: str) -> Optional[str]:
    """
    Write the SKILL.md to disk under <skills_dir>/<skill-name>/SKILL.md.

    Uses a content hash suffix to prevent overwriting manually edited skills
    while still skipping truly identical content.

    Returns the created directory path, or None on failure.
    """
    skill_name = _extract_skill_name(skill_content)
    if not skill_name:
        logger.warning("[Distill] Could not extract skill name from generated content.")
        return None

    # Ensure auto-generated skills have the prefix
    if not skill_name.startswith(AUTO_SKILL_PREFIX):
        skill_name = AUTO_SKILL_PREFIX + skill_name

    content_hash = _compute_content_hash(skill_content)
    skill_dir = os.path.join(skills_dir, skill_name)

    # Deduplication: if a dir with same name exists and content matches, skip
    existing_skill_md = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(existing_skill_md):
        try:
            with open(existing_skill_md, "r", encoding="utf-8") as f:
                existing_content = f.read()
            if _compute_content_hash(existing_content) == content_hash:
                logger.debug(f"[Distill] Skill '{skill_name}' already exists with identical content, skipping.")
                return None
        except Exception:
            pass
        # Content differs — use hash-suffixed name to avoid collision
        skill_name = f"{skill_name}-{content_hash}"
        skill_dir = os.path.join(skills_dir, skill_name)

    os.makedirs(skill_dir, exist_ok=True)
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(skill_content)
        logger.info(f"[Distill] ✅ New skill saved: {skill_md_path}")
        return skill_dir
    except Exception as e:
        logger.error(f"[Distill] Failed to write skill file: {e}")
        return None


def _trigger_skill_manager_refresh(workspace_dir: str) -> None:
    """
    Ask the SkillManager in all running Agent instances to reload skills
    so the new skill becomes available in the next conversation turn.
    Uses the same Bridge access pattern as cow_cli.py.
    """
    try:
        from bridge.bridge import Bridge
        agent_bridge = Bridge().get_agent_bridge()
        if not agent_bridge:
            return
        # Refresh default agent and all session agents
        agents_to_refresh = []
        if agent_bridge.default_agent:
            agents_to_refresh.append(agent_bridge.default_agent)
        agents_to_refresh.extend(agent_bridge.agents.values())
        refreshed = 0
        for agent in agents_to_refresh:
            if agent and hasattr(agent, 'skill_manager') and agent.skill_manager:
                agent.skill_manager.refresh_skills()
                refreshed += 1
                break  # One refresh is sufficient (shared skill directories)
        if refreshed:
            logger.debug(f"[Distill] SkillManager refreshed after distillation.")
    except Exception as e:
        logger.debug(f"[Distill] Could not trigger SkillManager refresh: {e}")


def _resolve_skills_dir(workspace_dir: str) -> Optional[str]:
    """
    Resolve and create the custom skills directory for the given workspace.
    Returns None if workspace_dir is not set.
    """
    if not workspace_dir:
        logger.debug("[Distill] No workspace_dir configured, skipping distillation.")
        return None

    # Expand ~ and env vars
    skills_dir = os.path.expanduser(os.path.join(workspace_dir, SKILLS_SUBDIR))
    os.makedirs(skills_dir, exist_ok=True)
    return skills_dir


def _distill_in_background(trajectory: str, model, skills_dir: str) -> Optional[str]:
    """
    Core distillation logic executed in the background thread.

    1. Build the reflection prompt.
    2. Call LLM for skill generation.
    3. Parse and validate the result.
    4. Write the SKILL.md to disk.
    5. Trigger SkillManager refresh.
    """
    logger.debug("[Distill] Starting reflection LLM call...")
    prompt = _build_reflection_prompt(trajectory)

    skill_content = _call_llm_for_reflection(prompt, model)
    if not skill_content:
        logger.debug("[Distill] No skill generated.")
        return None

    created_path = _save_skill(skill_content, skills_dir)
    if created_path:
        _trigger_skill_manager_refresh(os.path.dirname(skills_dir))

    return created_path
