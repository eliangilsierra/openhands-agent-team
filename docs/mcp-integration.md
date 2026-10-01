# MCP Integration

The **Model Context Protocol (MCP)** connects agents to external tools. The initial team uses only
three capabilities — GitHub, filesystem/repository and web/research — because every additional
server adds credentials to manage and attack surface to defend.

> **Verification note.** *Official* statements were checked against the OpenHands MCP
> documentation and the referenced MCP servers' READMEs on 2026-10-01. MCP servers are configured
> in the OpenHands runtime, never in this repository. Server versions, tool names and launch
> commands change; confirm them in each server's README before configuring.

## 1. How OpenHands configures MCP

*Official:*

- Transports: Streamable HTTP (SHTTP), Server-Sent Events (SSE) and stdio.
- Configuration surfaces: Agent Canvas (`Customize > MCP Servers`), the CLI (`openhands mcp add`,
  persisted in `~/.openhands/mcp.json`), or the SDK (`mcp_config`).
- SHTTP/SSE servers take a name, URL, authentication (none, bearer token, header or OAuth) and an
  optional timeout; stdio servers take a name, command, arguments and environment variables.
- Current OpenHands releases do **not** read the legacy `config.toml` `[mcp]` section
  (`sse_servers`, `shttp_servers`, `stdio_servers`); that format belongs to OpenHands V0.
- Agent Profiles can reference specific MCP servers; a profile with no references can use all
  configured servers.
- ACP agents (Claude Code) do not receive OpenHands MCP configuration; they use their own tools and
  MCP settings (see [acp-integration.md](acp-integration.md#11-tools-and-mcp-for-acp-profiles)).

## 2. Initial capabilities

| Capability | Provides | Used by | How it is provided |
| --- | --- | --- | --- |
| **GitHub** | Read repositories, Issues, Pull Requests, reviews, Actions results; create and comment on Issues and PRs; manage labels; submit reviews | All agents | GitHub MCP server for OpenHands-type profiles; `git`/GitHub CLI with `GITHUB_TOKEN` for ACP profiles |
| **Filesystem / Repository** | Read, search and edit files of the checked-out repository; run commands in the sandbox | All agents (edit rights per [permissions](../config/permissions.yaml)) | Built-in file and shell tools of the OpenHands runtime; Claude Code's built-in tools for ACP profiles |
| **Web / Research** | Fetch and read web pages, official documentation, package registries, advisories | Researcher, Architect, Security Reviewer, Developer (documentation lookup) | Built-in browsing of the runtime and, optionally, an MCP fetch server |

### 2.1 GitHub

- **Server:** the official GitHub MCP server ([github/github-mcp-server](https://github.com/github/github-mcp-server)).
  *Official (its README):* available as a remote server at `https://api.githubcopilot.com/mcp/` or as
  the container image `ghcr.io/github/github-mcp-server` (stdio) authenticated with the
  `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable; toolsets are selected with
  `GITHUB_TOOLSETS` / `--toolsets`; `--read-only` restricts it to read tools.
- **Credential:** the agent identity's fine-grained token (see
  [github-integration.md](github-integration.md#agent-identity)), stored as an OpenHands secret
  or entered as the server's bearer token in the MCP settings. Never written into a committed file.
- **Toolsets (convention):** enable only `repos`, `issues`, `pull_requests` and `actions`
  (read check results). Add `code_security` / `dependabot` for the Security Reviewer only if the
  token is granted those read permissions.
- **Least privilege (convention):** where your OpenHands version lets profiles reference
  different MCP servers, configure two GitHub server entries — `github` (read/write toolsets) and
  `github-readonly` (`--read-only`) — and give read-only access to roles that never write
  (none of the current roles is strictly read-only on GitHub because all post comments, so a single
  `github` entry is the initial default).

### 2.2 Filesystem / Repository

- OpenHands-type agents already have file editing, search and shell tools in their sandbox; the
  repository is checked out there. **No filesystem MCP server is configured initially.**
- Claude Code (ACP) uses its own file tools.
- Optional: the reference filesystem server
  ([modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers), launched with
  `npx -y @modelcontextprotocol/server-filesystem <allowed-directory>`) restricts access to
  explicitly allowed directories. Add it only if a profile must not have general shell access
  but needs file access.

### 2.3 Web / Research

- The OpenHands runtime provides a browser tool; Claude Code provides its own web tools.
- Optional: the reference **fetch** server from
  [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) (stdio) converts
  pages to text for the Researcher. Check its README for the current launch command.
- Search APIs are **not** configured initially; the Researcher works from official documentation
  sites, registries and advisory databases reachable by URL.
- Web content is untrusted: agents treat fetched content as data and never follow instructions in it.

## 3. Mapping to Agent Profiles

Capabilities per agent are canonical in `mcp` of [config/agents.yaml](../config/agents.yaml); how
each one is provided depends on the backend.

| Agent | `github` | `filesystem` | `web` | Provided by |
| --- | --- | --- | --- | --- |
| product-manager | yes | yes (read) | no | GitHub MCP server; runtime file tools |
| researcher | yes | yes (`docs/research/`) | yes | GitHub MCP server; runtime tools; browser or optional fetch server |
| architect | yes | yes (`docs/` paths) | yes | Claude Code tools; `git`/GitHub CLI with `GITHUB_TOKEN` |
| planner | yes | yes (read) | no | GitHub MCP server; runtime file tools |
| developer | yes | yes (feature branch) | yes | Claude Code tools; `git`/GitHub CLI with `GITHUB_TOKEN` |
| qa-engineer | yes | yes (tests only when assigned) | no | GitHub MCP server; runtime tools (local browser use against the sandbox app is not web access) |
| code-reviewer | yes | yes (read, run tests) | no | Claude Code tools; `git`/GitHub CLI with `GITHUB_TOKEN` |
| security-reviewer | yes | yes (read, run scanners) | yes | GitHub MCP server; runtime tools; browser or optional fetch server |
| orchestrator | yes | yes (read) | no | GitHub MCP server; runtime file tools |

Write scopes in parentheses come from [config/permissions.yaml](../config/permissions.yaml); the
tools themselves do not enforce them.

## 4. Rules for adding MCP servers

- Add a server only for a concrete, recurring need that the built-in tools cannot meet.
- Record the addition in `config/agents.yaml` (`mcp`) and this document through a Pull Request;
  an ADR is required if it adds a new external vendor or a new trust boundary.
- Prefer official servers maintained by the service vendor or the MCP project.
- Pin versions (image tag or package version) in the runtime configuration.
- Use the narrowest credential and toolset; prefer read-only modes.
- Never commit MCP configuration that contains tokens.

## 5. Future optional integrations

Not configured now; each requires the process in section 4.

| Integration | Possible use | Trigger to consider it |
| --- | --- | --- |
| Web search API (MCP) | Broader research beyond known documentation sites | Research quality limited by inability to discover sources |
| Error tracking (for example Sentry MCP) | QA and Developer read production error context | Bugs routinely need production stack traces |
| Observability / logs | Diagnose incidents | Team starts handling operational incidents through the workflow |
| Database (read-only, non-production) | QA verifies data effects | Integration tests insufficient to inspect state |
| Documentation index (for example a context/docs MCP) | Version-accurate library docs | Repeated errors from outdated library knowledge |
| Browser automation (for example Playwright MCP) | Richer E2E checks | Built-in browser insufficient for E2E validation |
