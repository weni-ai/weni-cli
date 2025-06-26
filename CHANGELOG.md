# Changelog

## [3.4.0] - 2025-06-26

### Added

- Fix: send preprocessor example and rename to pre_processing ([#117](https://github.com/weni-ai/weni-cli/pull/117)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Add validation when user not allowed to push ([#116](https://github.com/weni-ai/weni-cli/pull/116)) ([**@lucaslinhares**](https://github.com/lucaslinhares))
- Add validation to length in description tool ([#115](https://github.com/weni-ai/weni-cli/pull/115)) ([**@lucaslinhares**](https://github.com/lucaslinhares))

## [3.3.2] - 2025-05-30

## Added

- Improve errors messages in test definition ([#111](https://github.com/weni-ai/weni-cli/pull/111)) ([**@lucaslinhares**](https://github.com/lucaslinhares))

## [3.3.1] - 2025-05-28

### Added

- Update weni-agents-toolkit to version 2.2.1 ([#110](https://github.com/weni-ai/weni-cli/pull/110)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [3.3.0] - 2025-05-27

### Added

- Update Flask to version 3.1.1 in pyproject.toml ([#108](https://github.com/weni-ai/weni-cli/pull/108)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Update weni-agents-toolkit to version 2.2.0 ([#107](https://github.com/weni-ai/weni-cli/pull/107)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Update message when user get a 401 error ([#106](https://github.com/weni-ai/weni-cli/pull/106)) ([**@lucaslinhares**](https://github.com/lucaslinhares))
- Validation to avoid whitespaces in template name ([#105](https://github.com/weni-ai/weni-cli/pull/105)) ([**@lucaslinhares**](https://github.com/lucaslinhares))
- Validation to language in active agent definition ([#104](https://github.com/weni-ai/weni-cli/pull/104)) ([**@lucaslinhares**](https://github.com/lucaslinhares))

## [3.2.0] - 2025-05-20

### Added

- Feat: Add push for active agents ([#100](https://github.com/weni-ai/weni-cli/pull/100)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- add validation for active agents ([#99](https://github.com/weni-ai/weni-cli/pull/99)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [3.1.1] - 2025-05-08

### Added

- Refactor log retrieval CLI command ([#98](https://github.com/weni-ai/weni-cli/pull/98)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [3.1.0] - 2025-05-05

### Added

- Agent tool logs visualization ([#96](https://github.com/weni-ai/weni-cli/pull/96)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [3.0.0] - 2025-04-23

### Added

- Update YAML structure for API key credentials in documentation ([#94](https://github.com/weni-ai/weni-cli/pull/94)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor credential definitions in documentation for consistency ([#93](https://github.com/weni-ai/weni-cli/pull/93)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Update weni-agents-toolkit version to 2.0.0 in poetry.lock and pyproject.toml ([#92](https://github.com/weni-ai/weni-cli/pull/92)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor documentation and codebase to transition from 'skills' to 'tools' ([#91](https://github.com/weni-ai/weni-cli/pull/91)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor CLIClient and related handlers to use 'tool_key' and 'agent_key' terminology ([#90](https://github.com/weni-ai/weni-cli/pull/90)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor agent definition to replace 'skills' with 'tools' ([#89](https://github.com/weni-ai/weni-cli/pull/89)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.2.1] - 2025-04-10

### Added

- Add component validation to agent definition schema ([#86](https://github.com/weni-ai/weni-cli/pull/86)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat/enhance definition validation ([#85](https://github.com/weni-ai/weni-cli/pull/85)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor ProjectPushHandler and improve error handling in skill folder creation ([#84](https://github.com/weni-ai/weni-cli/pull/84)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Enhance error handling in RunHandler and definition validation ([#83](https://github.com/weni-ai/weni-cli/pull/83)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: Add mypy ([#82](https://github.com/weni-ai/weni-cli/pull/82)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.2.0] - 2025-03-27

### Added

- feat: update toolkit version to 1.0.0 ([#79](https://github.com/weni-ai/weni-cli/pull/79)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Add CLI version retrieval and include it in request headers ([#78](https://github.com/weni-ai/weni-cli/pull/78)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: Remove old build method and update dependencies ([#77](https://github.com/weni-ai/weni-cli/pull/77)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Add version flag to CLI and implement version printing utility ([#76](https://github.com/weni-ai/weni-cli/pull/76)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- add more agents examples and warnings for yaml elements ([#75](https://github.com/weni-ai/weni-cli/pull/75)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- remove weni version command ([#74](https://github.com/weni-ai/weni-cli/pull/74)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- add run content and glosary att ([#73](https://github.com/weni-ai/weni-cli/pull/73)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- Hotfix/new skills doc ([#72](https://github.com/weni-ai/weni-cli/pull/72)) ([**@johncordeiro**](https://github.com/johncordeiro))

## [2.1.0] - 2025-03-14

### Added

- Docs/content reformulation ([#70](https://github.com/weni-ai/weni-cli/pull/70)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- Feat: Add WeniClient tests ([#61](https://github.com/weni-ai/weni-cli/pull/61)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- test: add tests for handling unhandled exceptions in CLI commands ([#63](https://github.com/weni-ai/weni-cli/pull/63)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- test: enhance exception handling tests for directory and file operations in CLI commands ([#64](https://github.com/weni-ai/weni-cli/pull/64)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- test: add unit tests for Store class ([#65](https://github.com/weni-ai/weni-cli/pull/65)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- feat: add formatter module for CLI ([#66](https://github.com/weni-ai/weni-cli/pull/66)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- feat: implement project permission check in CLIClient and integrate with ProjectUseHandler ([#67](https://github.com/weni-ai/weni-cli/pull/67)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- feat: add agent definition schema validation ([#68](https://github.com/weni-ai/weni-cli/pull/68)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- feat: definition validator tests ([#69](https://github.com/weni-ai/weni-cli/pull/69)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

### Changed

- Refactor: CLI client ([#62](https://github.com/weni-ai/weni-cli/pull/62)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.0.4] - 2025-03-11

### Added

- refactor: update agent definition YAML template with dynamic test path ([#58](https://github.com/weni-ai/weni-cli/pull/58)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- test: add test suite for skill packager module ([#57](https://github.com/weni-ai/weni-cli/pull/57)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: Add run command tests ([#56](https://github.com/weni-ai/weni-cli/pull/56)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))


## [2.0.3] - 2025-03-08

### Changed

- fix: conditionally render test result panels only when logs exist ([#54](https://github.com/weni-ai/weni-cli/pull/54)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.0.2] - 2025-03-08

### Changed

- refactor: improve log rendering and verbose output handling ([#52](https://github.com/weni-ai/weni-cli/pull/52)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.0.1] - 2025-03-08

### Changed

- refactor: improve parameter validation type checking ([#50](https://github.com/weni-ai/weni-cli/pull/50)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [2.0.0] - 2025-03-08

### Added

- Feat: update init command with CEP agent and address skill ([#48](https://github.com/weni-ai/weni-cli/pull/48)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor: simplify skill source path retrieval ([#47](https://github.com/weni-ai/weni-cli/pull/47)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Refactor: simplify log formatting in run command ([#46](https://github.com/weni-ai/weni-cli/pull/46)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: update run command to use agent and skill keys ([#45](https://github.com/weni-ai/weni-cli/pull/45)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: add project UUID header to CLI client requests ([#44](https://github.com/weni-ai/weni-cli/pull/44)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: integrate rich-click for enhanced CLI help and formatting ([#43](https://github.com/weni-ai/weni-cli/pull/43)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: add run command for testing agent skills ([#42](https://github.com/weni-ai/weni-cli/pull/42)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: implement custom spinner with enhanced functionality ([#41](https://github.com/weni-ai/weni-cli/pull/41)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: add validators module for definition parsing and validation ([#40](https://github.com/weni-ai/weni-cli/pull/40)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: add skill packaging utility for creating zip archives ([#39](https://github.com/weni-ai/weni-cli/pull/39)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Feat: Use CLI Backend instead of Nexus ([#38](https://github.com/weni-ai/weni-cli/pull/38)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Update authentication.md ([#37](https://github.com/weni-ai/weni-cli/pull/37)) ([**@johncordeiro**](https://github.com/johncordeiro))
- Content adjustments ([#36](https://github.com/weni-ai/weni-cli/pull/36)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- Design, structure and content update ([#35](https://github.com/weni-ai/weni-cli/pull/35)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))

## [1.0.1] - 2025-02-07

### Changed

- Improved dependencies ([#32](https://github.com/weni-ai/weni-cli/pull/32)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

### Added

- Add CI and CD workflows ([#33](https://github.com/weni-ai/weni-cli/pull/33)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [1.0.0] - 2025-02-03

### Changed

- Update documentation with skill folder structure ([#29](https://github.com/weni-ai/weni-cli/pull/29)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Make project push use the new agent skill folder structure ([#28](https://github.com/weni-ai/weni-cli/pull/28)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

### Added

- New folder structure tests ([#30](https://github.com/weni-ai/weni-cli/pull/30)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Add skill parameters validation ([#27](https://github.com/weni-ai/weni-cli/pull/27)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.2.0] - 2025-01-22

### Added

- Unit tests to current and use commands ([#24](https://github.com/weni-ai/weni-cli/pull/24)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Unit tests to init command ([#23](https://github.com/weni-ai/weni-cli/pull/23)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Unit tests to project push ([#22](https://github.com/weni-ai/weni-cli/pull/22)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Unit tests to project list ([#21](https://github.com/weni-ai/weni-cli/pull/21)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Documentation with mkdocs ([#20](https://github.com/weni-ai/weni-cli/pull/20)) ([**@hugocarvalhopc**](https://github.com/hugocarvalhopc))
- Unit tests to login command ([#19](https://github.com/weni-ai/weni-cli/pull/19)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))
- Init command ([#18](https://github.com/weni-ai/weni-cli/pull/18)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.9] - 2025-01-15

### Added

- Project list pagination ([#17](https://github.com/weni-ai/weni-cli/pull/17)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.8] - 2025-01-10

### Changed

- Use default port ([#16](https://github.com/weni-ai/weni-cli/pull/16)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.7] - 2025-01-10

### Changed

- Default port to allow windows ([#15](https://github.com/weni-ai/weni-cli/pull/15)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.6] - 2025-01-10

### Added

- README.md ([#12](https://github.com/weni-ai/weni-cli/pull/12)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

### Changed 

- Use threads instead of processes ([#13](https://github.com/weni-ai/weni-cli/pull/13)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.5] - 2025-01-10

### Removed

- Windows subprocess fix ([#10](https://github.com/weni-ai/weni-cli/pull/10)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.4] - 2025-01-10

### Fixed

- Incorrect echo format ([#9](https://github.com/weni-ai/weni-cli/pull/9)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.3] - 2025-01-10

### Added

- Skill parameters and description ([#8](https://github.com/weni-ai/weni-cli/pull/8)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.2] - 2025-01-09

### Fixed

- Windows subprocess start requirements ([#7](https://github.com/weni-ai/weni-cli/pull/7)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.1] - 2025-01-08

### Fixed

- Setuptools config  ([#6](https://github.com/weni-ai/weni-cli/pull/6)) ([**@paulobernardoaf**](https://github.com/paulobernardoaf))

## [0.1.0] - 2025-01-08

🌱 Initial release.