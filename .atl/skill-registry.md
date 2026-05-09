# Skill Registry — KineIA

**Generated**: 2026-05-09
**Source**: User-level skills in ~/.config/opencode/skills/
**Note**: SDD skills (sdd-*), _shared, and skill-registry are excluded per scan rules.

## Skills

### branch-pr
- **Trigger**: Creating, opening, or preparing PRs for review
- **Path**: ~/.config/opencode/skills/branch-pr/SKILL.md

**Rules**:
- Never create PRs without checking issue existence first
- Run issue-first checks before PR creation
- Must validate branch naming conventions
- PR body must include summary, changes, testing notes
- Use gh CLI for all GitHub operations

### chained-pr
- **Trigger**: PRs over 400 lines, stacked PRs, review slices
- **Path**: ~/.config/opencode/skills/chained-pr/SKILL.md

**Rules**:
- Split oversized changes into chained PRs
- Each PR must be independently reviewable (<400 lines)
- Maintain dependency ordering across stacked PRs
- Each PR description must reference its chain position
- Tests and docs must stay with their code in each slice

### cognitive-doc-design
- **Trigger**: Writing guides, READMEs, RFCs, onboarding, architecture docs
- **Path**: ~/.config/opencode/skills/cognitive-doc-design/SKILL.md

**Rules**:
- Reduce cognitive load in all documentation
- Use hierarchical structure with progressive disclosure
- Keep each section focused on one concept
- Prefer examples over abstract explanations
- Include a "TL;DR" for long documents

### comment-writer
- **Trigger**: PR feedback, issue replies, reviews, Slack messages, GitHub comments
- **Path**: ~/.config/opencode/skills/comment-writer/SKILL.md

**Rules**:
- Write warm, direct collaboration comments
- Start with what works before suggesting changes
- Be specific with code references
- Suggest, don't command — use "Consider..." / "What about...?"
- Explain the "why" behind suggestions

### go-testing
- **Trigger**: Go tests, go test coverage, Bubbletea teatest, golden files
- **Path**: ~/.config/opencode/skills/go-testing/SKILL.md

**Rules**:
- Apply focused Go testing patterns (table-driven, golden files)
- Use teatest for Bubbletea component testing
- Coverage must meet project thresholds
- Tests must be deterministic and isolated
- Golden files for CLI/output testing

### issue-creation
- **Trigger**: Creating GitHub issues, bug reports, feature requests
- **Path**: ~/.config/opencode/skills/issue-creation/SKILL.md

**Rules**:
- Verify issue doesn't already exist before creating
- Include reproduction steps for bugs
- Use structured templates (bug/feature/enhancement)
- Tag with appropriate labels
- Include environment/version context

### judgment-day
- **Trigger**: Dual review, adversarial review, "juzgar"
- **Path**: ~/.config/opencode/skills/judgment-day/SKILL.md

**Rules**:
- Run blind dual review: two independent passes
- Fix confirmed issues only after both reviews agree
- Re-judge after fixes are applied
- Document false positives for pattern improvement
- Never reveal reviewer identity during blind phase

### omarchy
- **Trigger**: Linux desktop customization (Hyprland, Waybar, Walker, etc.)
- **Path**: ~/.claude/skills/omarchy/SKILL.md

**Rules**:
- REQUIRED for end-user Linux desktop config changes
- Affects ~/.config/hypr/, waybar/, walker/, alacritty/, kitty/, ghostty/, mako/, omarchy/
- Use for: window rules, animations, keybindings, monitors, themes, wallpaper, etc.
- Excludes Omarchy source development in ~/.local/share/omarchy/
- Never modify system files outside user config dirs

### skill-creator
- **Trigger**: New skills, agent instructions, documenting AI usage patterns
- **Path**: ~/.config/opencode/skills/skill-creator/SKILL.md

**Rules**:
- Create LLM-first skills with valid frontmatter
- Required structure: Activation Contract, Hard Rules, Decision Gates, Execution Steps, Output Contract, References
- Keep description quoted, one line, ≤250 chars
- Target 180-450 body tokens; move extended content to references/
- Quality gates: hard rules are observable, decision gates cover real forks

### work-unit-commits
- **Trigger**: Implementation, commit splitting, chained PRs
- **Path**: ~/.config/opencode/skills/work-unit-commits/SKILL.md

**Rules**:
- Plan commits as reviewable work units
- Keep tests and docs with their code
- Each commit must be independently reviewable
- No "wip" or "fixup" commits in PRs
- Follow conventional commits format

## Convention Files

No project-level convention files found (no AGENTS.md, CLAUDE.md, .cursorrules, etc. in project root).
