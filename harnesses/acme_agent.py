"""Remediated Acme Corp Enterprise Knowledge-Work Agent Harness (acme_agent.py).

FIXES APPLIED:
  1. Uses the `google-genai` SDK (`genai.Client(vertexai=True)`) with
     `gemini-3.1-pro-preview` and matched `ThinkingConfig(thinking_level="HIGH")`
     (without setting deprecated `temperature`).
  2. Uses native structured Function Calling (`run_bash`, `finish_task`) and
     preserves the full `response.candidates[0].content` (including `thought_signature`).
  3. Returns full `stdout` AND `stderr` on non-zero exit codes so the model can
     self-correct SQL/Python errors in 1 turn instead of guessing blindly.
  4. Enforces Commit-and-Verify discipline (`max_turns = 20` + 2-turn warning)
     before turn-cap expiration.
"""

from pathlib import Path
from typing import override

from google import genai
from google.genai import types
from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


RUN_BASH_DECL = types.FunctionDeclaration(
    name="run_bash",
    description=(
        "Execute a bash command inside `/workspace` and return exit_code, "
        "stdout, and stderr."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to run in /workspace.",
            }
        },
        "required": ["command"],
    },
)

FINISH_TASK_DECL = types.FunctionDeclaration(
    name="finish_task",
    description=(
        "Signal that all required deliverables (JSON reports and "
        "/workspace/answer.md) have been written and verified."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief summary of verified deliverables.",
            }
        },
        "required": ["summary"],
    },
)


class AcmeAgent(BaseAgent):
  """Fair, well-engineered Vertex AI Gemini 3 agent harness."""

  @staticmethod
  @override
  def name() -> str:
    return "acme-agent"

  @override
  def version() -> str:
    return "2.0.0-fair"

  @override
  async def setup(self, environment: BaseEnvironment) -> None:
    return

  @override
  async def run(
      self,
      instruction: str,
      environment: BaseEnvironment,
      context: AgentContext,
  ) -> None:
    client = genai.Client(vertexai=True)
    model_id = self.model_name or "gemini-3.1-pro-preview"
    max_turns = 20

    system_instruction = (
        "You are an expert enterprise analyst operating in `/workspace`. "
        "Inspect all input files and schemas before computing results. "
        "Before calling `finish_task`, verify that every required output file "
        "(including `/workspace/answer.md`) exists and is non-empty."
    )

    history: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=instruction)],
        )
    ]

    for turn in range(1, max_turns + 1):
      # FIX 4 (Turn-Cap Guard): Warn the agent when 2 turns remain so it commits
      # its deliverables instead of timing out with an empty /workspace/answer.md.
      if turn == max_turns - 1:
        history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "SYSTEM NOTICE: 2 turns remaining. Write all final "
                            "deliverable files and `/workspace/answer.md` now, "
                            "then call `finish_task`."
                        )
                    )
                ],
            )
        )

      response = client.models.generate_content(
          model=model_id,
          contents=history,
          config=types.GenerateContentConfig(
              system_instruction=system_instruction,
              max_output_tokens=8192,
              # FIX 1: Proper Gemini 3 ThinkingConfig on Vertex AI
              thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
              tools=[
                  types.Tool(
                      function_declarations=[RUN_BASH_DECL, FINISH_TASK_DECL]
                  )
              ],
          ),
      )

      candidate_content = response.candidates[0].content
      # FIX 2: Append candidate_content directly so Gemini 3 `thought_signature`
      # parts are preserved across multi-turn tool calls!
      history.append(candidate_content)

      function_calls = response.function_calls or []
      if not function_calls:
        continue

      tool_response_parts: list[types.Part] = []
      done = False
      for fc in function_calls:
        if fc.name == "finish_task":
          done = True
          tool_response_parts.append(
              types.Part.from_function_response(
                  name="finish_task",
                  response={"status": "completed"},
              )
          )
        elif fc.name == "run_bash":
          cmd = fc.args.get("command", "")
          exec_res = await environment.exec(command=cmd)
          # FIX 3: Return BOTH stdout and stderr on non-zero exit codes!
          tool_response_parts.append(
              types.Part.from_function_response(
                  name="run_bash",
                  response={
                      "exit_code": exec_res.return_code,
                      "stdout": exec_res.stdout or "",
                      "stderr": exec_res.stderr or "",
                  },
              )
          )

      history.append(types.Content(role="user", parts=tool_response_parts))
      if done:
        break

    Path(self.logs_dir / "output.txt").write_text("Completed agent run.")
