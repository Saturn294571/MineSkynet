# Gate E0 검사 증거 — 2026-08-20

문서 역할: 모델과 planner를 제외한 Minecraft 실행 계층이 기존 Odyssey skill을 반복 실행하고 실패 뒤 복구할 수 있음을 입증하는 원시 증거다. Odyssey 전체 논문 재현을 의미하지 않는다.

이 문서는 `e0-executor` 후보 환경에서 수행한 정적 검사와 실제 Minecraft 회귀 시험의 압축 증거다. 원시 world와 cache는 Git 밖의 `Odyssey/runtime/`에 유지한다.

## 환경 snapshot

- Git 기준 commit: `80a42fcbd2b5da53ecf7e58f1036981e428c9590` (`origin/experiment/mvp-core`), 검사 시점에는 E0 관련 미커밋 변경이 존재했다.
- Docker image: `itzg/minecraft-server:java17`, image ID `sha256:5b3e96bcd7dace8ab7be89c245dc9ba0b1573fdef2f01d3e101ac40e7843fa70`
- Minecraft `1.19.4`, Fabric Loader `0.15.11`, Java `17.0.15+6`
- world seed: `7634567288700934061`
- Node `20.13.1`, npm `10.5.2`
- offline-mode bot operator UUID: `67128b5b-2e6b-3ad1-baa0-1b937b03e5c5` (`OfflinePlayer:bot`), repository profile `Odyssey/server-profile/e0/ops.json`
- `package-lock.json` SHA-256: `5555e896e0c5d19c635965bc9338b0cd60a248092bc9c8ff65a6c678943a6b7c`
- 직접 Node dependency: `mineflayer 4.25.0`, `minecraft-data 3.83.0`, `mineflayer-pathfinder 2.4.2`, `mineflayer-tool 1.2.0`, local `mineflayer-collectblock 1.4.1`, `express 4.18.2`, `vec3 0.1.8`, `typescript 4.9.5`, `@types/node 18.19.130`, `prismarine-entity 2.4.0`, `prismarine-item 1.15.0`
- `npm ci` 감사 결과: 16 vulnerabilities(3 low, 6 moderate, 7 high). 호환 묶음을 임의 변경하지 않기 위해 `npm audit fix`는 실행하지 않았다.

기존 modded fixture의 JAR SHA-256:

- Multiplayer Server Pause 1.3.1: `fe6fe7e5c398415578f2be355de4bcd74ed5f11ebb5929d1aa91381fa8074d24`
- CompleteConfig 2.3.1: `f7d5c7c82df363305b726f6fad651a68dad8404322d4b7a0f46d948882affcc2`
- Fabric API 0.87.2+1.19.4: `a92650d48a9f672dc74e8b1eaefedb28dc83a13a80431215900181aa3a8675d8`
- iChunUtil 1.0.2: `661b800c180d8f0dfca2467bebfbd57c41cd6b9e22cac989fb8979e3137d6475`

## 검사 결과

1. 활성 dependency tree에서 과거 `mineflayer-collectblock/node_modules`를 분리한 뒤 `npm ci`가 성공했다.
2. `npm run check`가 local collectblock TypeScript build, `node --check index.js`, `npm ls --depth=0`을 모두 통과했다. `npm ci` 뒤에도 하위 `mineflayer-collectblock/node_modules`는 생성되지 않았다.
3. `/health`와 `/version`은 pinned target Minecraft `1.19.4`와 위 dependency version을 반환했다.
4. modded fixture에서 bot 연결과 finite position을 0·5·10·15·20·25·30초에 확인했고 7/7 통과했다.
5. 매회 hard reset과 빈 인벤토리로 raw `mineWoodLog`를 10회 실행했다. 10/10에서 before `{}`, after `spruce_log: 1`, log delta `+1`, `onError: []`였다.
6. 매회 hard reset과 빈 인벤토리로 raw `craftCraftingTable`을 10회 실행했다. 10/10에서 before `{}`, after `crafting_table: 1`, table delta `+1`, `onError: []`였다.
7. clean `npm ci` 직후 30초 연결, 원목 1회, 작업대 1회를 다시 실행해 모두 통과했다.
8. 별도 임시 Fabric 서버는 같은 image ID·Minecraft·Fabric Loader·seed를 사용하되 외부 mod JAR를 하나도 넣지 않았다. 서버 로그의 mod 목록은 Minecraft, Java, Fabric Loader와 내장 MixinExtras뿐이었다.
9. 이 mod-free 서버에 `soft`로 접속해 finite position 30초, 원목 채집, 빈 인벤토리에서 작업대 제작을 각각 통과했다. 이 경로는 `/health`, `/start`, `/step`만 호출했고 `/pause`를 호출하지 않았다. 따라서 raw E0 실행에는 Multiplayer Server Pause, iChunUtil, CompleteConfig, Fabric API가 필요하지 않다.
10. `/start`가 요청별 bot instance를 캡처하도록 바꾸고 pending start 응답과 old-bot disconnect를 분리했다. 연속 hard `/start` 2회 뒤 15초 생존, 잘못된 port의 400 응답 뒤 bridge 생존·정상 hard reset 복구, 의도적인 `/step` 오류 뒤 연결 유지를 통과했다.
11. 새 offline-mode server에서 `OPS=bot`이 online UUID를 기록하는 문제를 확인했다. 올바른 offline UUID를 담은 `OPS_FILE`을 Compose에 고정한 뒤 외부 mod 없는 완전히 새 server의 첫·두 번째 hard reset, 15초 finite position, 원목과 작업대를 통과했다.
12. `Odyssey/scripts/e0_regression.py`로 기존 fixture에서 hard reset 기반 원목 10회와 작업대 10회를 재실행했다. 총 20/20, 모든 목표 delta `+1`, 모든 `onError: []`였다.
13. 원목 action latency는 평균 10,829.307 ms, P95 20,384.104 ms였고 작업대는 평균 13,172.842 ms, P95 23,990.514 ms였다.

## 해결된 결함과 보존 위치

- old bot의 늦은 disconnect가 새 전역 bot을 종료하던 경합은 request-local bot capture와 identity check로 해결했다.
- `/step` process-level exception listener는 request-local bot을 사용하고 response `finish`/`close`에서 정리한다. 실패 후 bridge 생존 회귀를 통과했다.
- 새 offline server의 hard reset timeout은 잘못된 online OP UUID가 원인이었다. Compose가 추적 가능한 offline UUID `OPS_FILE`을 사용하도록 수정했다.
- 최종 raw 결과는 `Odyssey/odyssey/env/results/e0/20260820T021925+0900/`에 있다. `environment.json`, 실행별 JSON 20개, `summary.json`, `minecraft_latest.log`를 포함하며 local runtime 결과라 Git에서 제외된다.
- 검사 당시에는 성공 commit/tag를 만들지 않았다. 이후 변경을 `a157205` (`E0 finished`)에 커밋하고 `odyssey-modernized-executor-1.19.4` annotated tag로 로컬·원격에 고정했다.
