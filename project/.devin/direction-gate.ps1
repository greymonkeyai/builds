# Direction gate (UserPromptSubmit): injects the cycle-gate rule into the agent's context.
# A stricter check — e.g. detecting ambiguous directions — evolves per project with use.
@{
  hookSpecificOutput = @{
    hookEventName    = 'UserPromptSubmit'
    additionalContext = 'Cycle gate: clarify the direction sufficiently before building; reject ambiguous directions as inadequate rather than running them.'
  }
} | ConvertTo-Json -Depth 5 -Compress
