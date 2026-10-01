**Research report** · Researcher · state: research

# Research: <question in one line>

<!--
Owner: Researcher · Skill: skills/research/SKILL.md
Persist as: comment on the research Issue; optionally docs/research/<issue>-<slug>.md via a docs/ PR.
Every finding carries exactly one label: FACT, EVIDENCE, ASSUMPTION, INTERPRETATION, RECOMMENDATION.
Cite only sources opened in this session. Record version/date and access date for each source.
-->

**Issue:** #<n> · **Requested by:** <role or @human> · **Time box:** <hours> · **Date:** <YYYY-MM-DD>

## Summary

- **Recommendation:** <one sentence> (R-<n>)
- **Confidence:** High | Medium | Low — <why>
- **Would change if:** <new information that would reverse the recommendation>

## Question

- **Decision supported:** <the decision someone will make with this report>
- **Sub-questions:** <1. …, 2. …>
- **Evaluation criteria (weight):** <criterion (high/medium/low)>
- **Constraints:** <versions, licences, hosting, budget, existing stack>

## Search strategy

| Priority | Source type | Sources / queries | Consulted | Useful |
| --- | --- | --- | --- | --- |
| 1 | Official documentation | <docs site, version> | yes / no | yes / no |
| 2 | Primary sources | <repository, changelog, RFC> | yes / no | yes / no |
| 3 | Maintainers | <issue thread, talk> | yes / no | yes / no |
| 4 | Reputable technical sources | <advisory DB, engineering blog> | yes / no | yes / no |
| 5 | Community | <forum thread> | yes / no | yes / no |

## Findings

| ID | Label | Statement | Source / basis |
| --- | --- | --- | --- |
| F-1 | FACT | <verified statement> | <URL> (version/date, accessed YYYY-MM-DD) or reproduction in Appendix |
| E-1 | EVIDENCE | <who claims what> | <URL> (date, accessed YYYY-MM-DD) |
| A-1 | ASSUMPTION | <unverified belief> | Verify by: <check> |
| I-1 | INTERPRETATION | <reasoning> | Based on: F-1, E-1 |

## Options compared

| Criterion | <Option A> | <Option B> | Keep current / do nothing |
| --- | --- | --- | --- |
| <criterion> | <assessment + finding IDs> | <assessment + finding IDs> | <assessment> |
| Security (CVEs, maintenance) | | | |
| Licence | | | |
| Operational cost / complexity | | | |

## Trade-offs

- **<Option A>:** gains <…>; gives up <…>.
- **<Option B>:** gains <…>; gives up <…>.

## Recommendation

| ID | Label | Recommendation | Relies on | Confidence |
| --- | --- | --- | --- | --- |
| R-1 | RECOMMENDATION | <action> | I-1, F-1 | High / Medium / Low |

## Unknowns

| Unknown | Why it matters | How to resolve |
| --- | --- | --- |
| <gap> | <impact on decision> | <spike, question to vendor, measurement> |

## Appendix: reproductions

```text
<commands run in the sandbox and their relevant output>
```
