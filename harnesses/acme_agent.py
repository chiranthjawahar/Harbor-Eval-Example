"""Acme Corp Enterprise Knowledge-Work Agent Harness (acme_agent.py)."""

from pathlib import Path
import re
from typing import override

from google import genai
from google.genai import types
from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class AcmeAgent(BaseAgent):
  """Acme Corp custom agent harness for enterprise knowledge-work evaluation."""

  @staticmethod
  @override
  def name() -> str:
    return "acme-agent"

  @override
  def version(self) -> str:
    return "0.9.0"

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

    system_prompt = (
        "You are an enterprise knowledge assistant. To run a shell command in "
        "the workspace, wrap it in <bash>...</bash> tags. When finished, output "
        "TASK_COMPLETE."
    )

    history: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"{system_prompt}\n\n{instruction}")],
        )
    ]

    max_turns = 8
    for _ in range(max_turns):
      response = client.models.generate_content(
          model=model_id,
          contents=history,
          config=types.GenerateContentConfig(
              max_output_tokens=1024,
              thinking_config=types.ThinkingConfig(thinking_level="LOW"),
          ),
      )
      text = response.text or ""
      history.append(
          types.Content(role="model", parts=[types.Part.from_text(text=text)])
      )

      if "TASK_COMPLETE" in text:
        break

      match = re.search(r"<bash>(.*?)</bash>", text, re.DOTALL)
      if not match:
        observation = "No <bash>...</bash> block detected. Please try again."
      else:
        cmd = match.group(1).strip()
        exec_res = await environment.exec(command=cmd)
        if exec_res.return_code != 0:
          observation = (
              f"Error: Command exited with status {exec_res.return_code}."
          )
        else:
          observation = exec_res.stdout or "(command succeeded with no output)"

      history.append(
          types.Content(
              role="user", parts=[types.Part.from_text(text=observation)]
          )
      )

    Path(self.logs_dir / "output.txt").write_text("Completed agent run.")
