# Changelog

<!--next-version-placeholder-->

## v2.3.2 (2023-11-02)

### Fix

* Ensure keep alives are disabled after stop ([#146](https://github.com/bdraco/yalexs-ble/issues/146)) ([`f4ec54d`](https://github.com/bdraco/yalexs-ble/commit/f4ec54d1dfa816152a44efda2871ec7cc016e433))

## v2.3.1 (2023-10-21)

### Fix

* Avoid state callbacks when nothing has changed ([#136](https://github.com/bdraco/yalexs-ble/issues/136)) ([`c4d3bc8`](https://github.com/bdraco/yalexs-ble/commit/c4d3bc89d797b6a9d8e9e564f14362041e8ec265))

## v2.3.0 (2023-09-09)

### Feature

* Switch to asyncio.timeout on py3.11+ ([#134](https://github.com/bdraco/yalexs-ble/issues/134)) ([`bce9605`](https://github.com/bdraco/yalexs-ble/commit/bce9605eb49a5d03512e7875c97f8695b665ca97))

## v2.2.3 (2023-07-20)

### Fix

* Use async-interrupt to avoid race in write ([#133](https://github.com/bdraco/yalexs-ble/issues/133)) ([`436f57b`](https://github.com/bdraco/yalexs-ble/commit/436f57bc230d58721c2221077f51340aa6866524))

## v2.2.2 (2023-07-20)

### Fix

* Ensure task is uncancelled when catching CancelledError and re-raising as different exception ([#132](https://github.com/bdraco/yalexs-ble/issues/132)) ([`a4dc7ed`](https://github.com/bdraco/yalexs-ble/commit/a4dc7ed8c605b3996ca015109ca900aef6372b17))

## v2.2.1 (2023-07-18)

### Fix

* Ensure cancellation is propagated during write if it is not from a disconnect ([#131](https://github.com/bdraco/yalexs-ble/issues/131)) ([`dd65807`](https://github.com/bdraco/yalexs-ble/commit/dd65807d5dbf42387c0e46d2836af89a9876b4e7))

## v2.2.0 (2023-07-13)

### Feature

* Refactor to avoid asyncio.wait and task creation during write ([#129](https://github.com/bdraco/yalexs-ble/issues/129)) ([`ae0ea36`](https://github.com/bdraco/yalexs-ble/commit/ae0ea3609371f2383f1aa66cb1a727732300f03d))

## v2.1.18 (2023-06-13)
### Fix
* Reduce battery drain when advertisement changes frequently ([#128](https://github.com/bdraco/yalexs-ble/issues/128)) ([`7f3fdfd`](https://github.com/bdraco/yalexs-ble/commit/7f3fdfd55bc4c004d89f4a377aa37d2b31d0f968))

## v2.1.17 (2023-05-16)
### Fix
* Guard against reconnecting after shutdown ([#127](https://github.com/bdraco/yalexs-ble/issues/127)) ([`1499acb`](https://github.com/bdraco/yalexs-ble/commit/1499acb68fc85a660c326f237c003d0cdc8ebaf4))

## v2.1.16 (2023-04-25)
### Fix
* Handle flakey authentication with 1.3.4 firmware ([#125](https://github.com/bdraco/yalexs-ble/issues/125)) ([`21d20c9`](https://github.com/bdraco/yalexs-ble/commit/21d20c9609ca08315eb2fe83e86d4aeffe0932e8))

## v2.1.15 (2023-04-25)
### Fix
* Handling of cancellation of first update ([#124](https://github.com/bdraco/yalexs-ble/issues/124)) ([`a850330`](https://github.com/bdraco/yalexs-ble/commit/a850330260c3634faddb2e947cd18a446d61bef7))

## v2.1.14 (2023-03-29)
### Fix
* Skip status for door/battery/lock if an update came over unsolicited notify ([#123](https://github.com/bdraco/yalexs-ble/issues/123)) ([`b41d579`](https://github.com/bdraco/yalexs-ble/commit/b41d57920374c6922ba0832a383d00954f6b0c70))

## v2.1.13 (2023-03-29)
### Fix
* Seperate door and lock status ([#121](https://github.com/bdraco/yalexs-ble/issues/121)) ([`36abe23`](https://github.com/bdraco/yalexs-ble/commit/36abe238c5554427a72da35ee84a9f03194856fa))

## v2.1.12 (2023-03-27)
### Fix
* Always stop notify before shutting down the session ([#122](https://github.com/bdraco/yalexs-ble/issues/122)) ([`fa7354d`](https://github.com/bdraco/yalexs-ble/commit/fa7354d95ba564f3567c9dfd4b74be0cff00d366))

## v2.1.11 (2023-03-27)
### Fix
* Implement a cooldown between commands ([#120](https://github.com/bdraco/yalexs-ble/issues/120)) ([`fd81a67`](https://github.com/bdraco/yalexs-ble/commit/fd81a670e5178f8f4ef839c91fc45fd64f5074f8))

## v2.1.10 (2023-03-27)
### Fix
* Allow cancelation during update to raise ([#118](https://github.com/bdraco/yalexs-ble/issues/118)) ([`b1456d5`](https://github.com/bdraco/yalexs-ble/commit/b1456d56db4aba3639f98004879c81a2932d74f2))

## v2.1.9 (2023-03-26)
### Fix
* Add some more debug logging for command execution ([#117](https://github.com/bdraco/yalexs-ble/issues/117)) ([`17b58f7`](https://github.com/bdraco/yalexs-ble/commit/17b58f75b7cebc5ac4215dc44f257238c43e186a))

## v2.1.8 (2023-03-26)
### Fix
* Delay disconnect after initial sync if another sync is pending ([#116](https://github.com/bdraco/yalexs-ble/issues/116)) ([`1dfdf2a`](https://github.com/bdraco/yalexs-ble/commit/1dfdf2a9479f3bc3429b53ae774868b8f53f8302))

## v2.1.7 (2023-03-26)
### Fix
* Handle bad gatt cache during sessions setup ([#115](https://github.com/bdraco/yalexs-ble/issues/115)) ([`9032049`](https://github.com/bdraco/yalexs-ble/commit/9032049316bb67f9c2b6bf04c1cbfcc772045456))

## v2.1.6 (2023-03-26)
### Fix
* Force a reconnect when the lock is in a bad state ([#114](https://github.com/bdraco/yalexs-ble/issues/114)) ([`ab40867`](https://github.com/bdraco/yalexs-ble/commit/ab408673b455eaad180fbaebf1f0a0bf48a2b9d0))

## v2.1.5 (2023-03-25)
### Fix
* Increase stale state debounce to 6.1s ([#113](https://github.com/bdraco/yalexs-ble/issues/113)) ([`25b6c09`](https://github.com/bdraco/yalexs-ble/commit/25b6c0992ae4d4902322de03a53f16c76eeb0f20))

## v2.1.4 (2023-03-25)
### Fix
* Increase stale state debounce delay to 4.0s ([#112](https://github.com/bdraco/yalexs-ble/issues/112)) ([`bb7081c`](https://github.com/bdraco/yalexs-ble/commit/bb7081cb024de689495bfc07bd8d5d3fb9934e08))

## v2.1.3 (2023-03-25)
### Fix
* Avoid updating state until 3 seconds after a lock operation to avoid stale state ([#111](https://github.com/bdraco/yalexs-ble/issues/111)) ([`c4ce2a1`](https://github.com/bdraco/yalexs-ble/commit/c4ce2a1b9f0c47b2aeeacadf907eb897dc0acd68))

## v2.1.2 (2023-03-23)
### Fix
* Handle missing characteristic when reading lock info ([#110](https://github.com/bdraco/yalexs-ble/issues/110)) ([`1bc667d`](https://github.com/bdraco/yalexs-ble/commit/1bc667d4d78f7f753fd2521951166c58bee412da))

## v2.1.1 (2023-03-21)
### Fix
* Hold a reference to the deferred update task to avoid GC ([#109](https://github.com/bdraco/yalexs-ble/issues/109)) ([`ddb5539`](https://github.com/bdraco/yalexs-ble/commit/ddb5539327a7fb3f20fefee180f36d78ed7c4e39))

## v2.1.0 (2023-03-16)
### Feature
* Switch to using cryptography ([#108](https://github.com/bdraco/yalexs-ble/issues/108)) ([`8acc73c`](https://github.com/bdraco/yalexs-ble/commit/8acc73c6dba8db242f33f9896ff5f2cf92ce5a2d))

## v2.0.4 (2023-02-26)
### Fix
* Handle transient auth failures ([#107](https://github.com/bdraco/yalexs-ble/issues/107)) ([`d7f8e14`](https://github.com/bdraco/yalexs-ble/commit/d7f8e14de39d2571deffed68e4ef2fb64d83bdcf))

## v2.0.3 (2023-02-23)
### Fix
* Ensure first update bluetooth errors are converted to YaleXSBLEError ([#106](https://github.com/bdraco/yalexs-ble/issues/106)) ([`ab96193`](https://github.com/bdraco/yalexs-ble/commit/ab96193e4b21688ca8c91e179ca5952c84e4f3c3))

## v2.0.2 (2023-02-20)
### Fix
* Always request disconnect even if we think we are connected to fix race ([#105](https://github.com/bdraco/yalexs-ble/issues/105)) ([`265fe8c`](https://github.com/bdraco/yalexs-ble/commit/265fe8c76d6b0bf31174e0d76ee22a19b52734b2))

## v2.0.1 (2023-02-17)
### Fix
* Handle the key changing after first connection ([#104](https://github.com/bdraco/yalexs-ble/issues/104)) ([`f8c2b91`](https://github.com/bdraco/yalexs-ble/commit/f8c2b91a1fc5617301f9625ab43ede1e5c1d61f4))

## v2.0.0 (2023-02-08)
### Feature
* Add wait_for_first_update to improve authentication error handling ([#103](https://github.com/bdraco/yalexs-ble/issues/103)) ([`6af1ec8`](https://github.com/bdraco/yalexs-ble/commit/6af1ec8394a13f77225c736bcf19a6b35539ea01))

### Breaking
* wait_for_first_update needs to be called after calling start before using the lock ([`6af1ec8`](https://github.com/bdraco/yalexs-ble/commit/6af1ec8394a13f77225c736bcf19a6b35539ea01))

## v1.12.12 (2023-02-08)
### Fix
* Raise AuthFailed when lock drops connection due to bad key with esphome proxies ([#102](https://github.com/bdraco/yalexs-ble/issues/102)) ([`c41cda5`](https://github.com/bdraco/yalexs-ble/commit/c41cda5a79578e6e1f26d28a483dbcb1f602954e))

## v1.12.11 (2023-02-07)
### Fix
* Raise AuthError when lock drops connection due to invalid key ([#101](https://github.com/bdraco/yalexs-ble/issues/101)) ([`7afffc5`](https://github.com/bdraco/yalexs-ble/commit/7afffc594250e50579c344b71e02be8db2b1e6e6))

## v1.12.10 (2023-02-07)
### Fix
* Ensure ble connection is cleaned up if connection setup fails ([#98](https://github.com/bdraco/yalexs-ble/issues/98)) ([`d5b34a6`](https://github.com/bdraco/yalexs-ble/commit/d5b34a637c84223ab0c9d169780610dffacd846e))

## v1.12.9 (2023-02-07)
### Fix
* Update isort to fix ci ([#99](https://github.com/bdraco/yalexs-ble/issues/99)) ([`10f174b`](https://github.com/bdraco/yalexs-ble/commit/10f174ba959c21baa692116671424dcd331a86f9))

## v1.12.8 (2023-01-23)
### Fix
* Wrap the disconnect waiter for py311 asyncio.wait requirements ([#97](https://github.com/bdraco/yalexs-ble/issues/97)) ([`ccb7f50`](https://github.com/bdraco/yalexs-ble/commit/ccb7f500ccae35a0735c83a30788f0a274d8685d))

## v1.12.7 (2023-01-22)
### Fix
* Improve unexpected disconnect handling ([#95](https://github.com/bdraco/yalexs-ble/issues/95)) ([`7a5ee06`](https://github.com/bdraco/yalexs-ble/commit/7a5ee06142fa2f79761403307aaf16310f92f170))

## v1.12.6 (2023-01-22)
### Fix
* Handle null bytes in the model/manufacturer data ([#94](https://github.com/bdraco/yalexs-ble/issues/94)) ([`6f04e4b`](https://github.com/bdraco/yalexs-ble/commit/6f04e4bc149b98ed1f9712052faa40520be7aafe))

## v1.12.5 (2022-12-23)
### Fix
* Ensure locked_writes raise after 3 failures ([#93](https://github.com/bdraco/yalexs-ble/issues/93)) ([`aac8b72`](https://github.com/bdraco/yalexs-ble/commit/aac8b72628f8a719a6e890de396af74c05af0be8))

## v1.12.4 (2022-12-23)
### Fix
* Ensure we still disconnect if the write times out ([#92](https://github.com/bdraco/yalexs-ble/issues/92)) ([`71655df`](https://github.com/bdraco/yalexs-ble/commit/71655df0be1b8a441e0924a87b6d00f9c10f21d7))

## v1.12.3 (2022-12-22)
### Fix
* Tell the device we are disconnecting ([#91](https://github.com/bdraco/yalexs-ble/issues/91)) ([`be60b5d`](https://github.com/bdraco/yalexs-ble/commit/be60b5df42b4e23234d8aca473e081adf2244f09))

## v1.12.2 (2022-12-17)
### Fix
* Check if disconnected before writing ([#90](https://github.com/bdraco/yalexs-ble/issues/90)) ([`4096eef`](https://github.com/bdraco/yalexs-ble/commit/4096eefbe85903e2602aabe3b189489fae744a55))
* Do not force a resync if previous state was unknown ([#89](https://github.com/bdraco/yalexs-ble/issues/89)) ([`84d82a7`](https://github.com/bdraco/yalexs-ble/commit/84d82a7300c4e49fe08aafa414236de4a84e56dd))

## v1.12.1 (2022-12-17)
### Fix
* Free up the connection faster after first update ([#88](https://github.com/bdraco/yalexs-ble/issues/88)) ([`5dfc984`](https://github.com/bdraco/yalexs-ble/commit/5dfc9844ccfb8a833574df3d94bbed06132641f3))

## v1.12.0 (2022-12-14)
### Feature
* Refactor to use a timed disconnect to improve reliablity ([#87](https://github.com/bdraco/yalexs-ble/issues/87)) ([`99323d8`](https://github.com/bdraco/yalexs-ble/commit/99323d8c82842c67dee7a9f60062f7c6b480069c))

## v1.11.4 (2022-12-10)
### Fix
* First update was scheduled being scheduled too late ([#86](https://github.com/bdraco/yalexs-ble/issues/86)) ([`eeb0ad4`](https://github.com/bdraco/yalexs-ble/commit/eeb0ad48ee4da3544520a01780de9f217c18fe40))

## v1.11.3 (2022-12-09)
### Fix
* Adjust battery percentage based on cliff calc ([#85](https://github.com/bdraco/yalexs-ble/issues/85)) ([`3e23368`](https://github.com/bdraco/yalexs-ble/commit/3e23368e746c77f9451caa484800b90612e51137))

## v1.11.2 (2022-12-09)
### Fix
* Adjust battery based on real world data ([#84](https://github.com/bdraco/yalexs-ble/issues/84)) ([`b1db44f`](https://github.com/bdraco/yalexs-ble/commit/b1db44fede827899ddeedb8c6111fce200abcff6))

## v1.11.1 (2022-12-09)
### Fix
* Adjust battery curve to better fit august values ([#83](https://github.com/bdraco/yalexs-ble/issues/83)) ([`0c5b888`](https://github.com/bdraco/yalexs-ble/commit/0c5b88817ff0124b2306e07b3dee50437b29295e))

## v1.11.0 (2022-12-09)
### Feature
* Add battery support ([#82](https://github.com/bdraco/yalexs-ble/issues/82)) ([`aeebae4`](https://github.com/bdraco/yalexs-ble/commit/aeebae47d112354851bd534bf611745a4d9e9d9a))

## v1.10.3 (2022-12-04)
### Fix
* Command execution tried to raise due to bad indent ([#81](https://github.com/bdraco/yalexs-ble/issues/81)) ([`99b9c4b`](https://github.com/bdraco/yalexs-ble/commit/99b9c4b2cf66d813b335206067486e84f13ed9d9))

## v1.10.2 (2022-12-03)
### Fix
* Task leak on destruction ([#80](https://github.com/bdraco/yalexs-ble/issues/80)) ([`900673c`](https://github.com/bdraco/yalexs-ble/commit/900673c2e496baae9b0fe629c5d7c0b3ca40d8bb))

## v1.10.1 (2022-12-03)
### Fix
* Detect missing characteristics and clear the cache ([#78](https://github.com/bdraco/yalexs-ble/issues/78)) ([`e921bf0`](https://github.com/bdraco/yalexs-ble/commit/e921bf009120d980a2502288cb006e2421396ddb))

## v1.10.0 (2022-12-01)
### Feature
* Add YaleXSBLEDiscovery class to be able to get discovery data from august cloud ([#77](https://github.com/bdraco/yalexs-ble/issues/77)) ([`28da7da`](https://github.com/bdraco/yalexs-ble/commit/28da7dad7e52c80182f3b938de0eb9fda07f51b7))

## v1.9.8 (2022-11-30)
### Fix
* Improve operation reliability ([#76](https://github.com/bdraco/yalexs-ble/issues/76)) ([`91f403f`](https://github.com/bdraco/yalexs-ble/commit/91f403f0fa6ace9bdfec6f5bd0694bbc124b84f0))

## v1.9.7 (2022-11-29)
### Fix
* Drop connection instead of executing shutdown ([#75](https://github.com/bdraco/yalexs-ble/issues/75)) ([`6d85edf`](https://github.com/bdraco/yalexs-ble/commit/6d85edfa2ac4286a5b05582907f19119939c6a71))

## v1.9.6 (2022-11-27)
### Fix
* Un-retrieved future exceptions when canceled ([#74](https://github.com/bdraco/yalexs-ble/issues/74)) ([`9c704dc`](https://github.com/bdraco/yalexs-ble/commit/9c704dc77b7791493d42621f77bbf3c51e87e75f))

## v1.9.5 (2022-10-31)
### Fix
* Lock advertisement state needs to be reset after going unavailable to ensure it becomes available again ([#73](https://github.com/bdraco/yalexs-ble/issues/73)) ([`cc1a252`](https://github.com/bdraco/yalexs-ble/commit/cc1a2529b4dd6406b71290bb83ec71fc9816cc51))

## v1.9.4 (2022-10-16)
### Fix
* Avoid logging failure when lock is already disconnected ([#72](https://github.com/bdraco/yalexs-ble/issues/72)) ([`08f562b`](https://github.com/bdraco/yalexs-ble/commit/08f562b57471247f3a0ff9f3622f4ae886ed2c77))

## v1.9.2 (2022-09-15)
### Fix
* Incorrect bleak-retry-connector version ([#70](https://github.com/bdraco/yalexs-ble/issues/70)) ([`d9c2708`](https://github.com/bdraco/yalexs-ble/commit/d9c2708aae8fbd1a3dc1c13bc34de6010affc11f))

## v1.9.1 (2022-09-15)
### Fix
* Handle additional bleak exceptions ([#69](https://github.com/bdraco/yalexs-ble/issues/69)) ([`bff64fc`](https://github.com/bdraco/yalexs-ble/commit/bff64fc296e0146f862e39e4c918ea51e516b244))

## v1.9.0 (2022-09-13)
### Feature
* Update for bleak 0.17 ([#67](https://github.com/bdraco/yalexs-ble/issues/67)) ([`78e00a0`](https://github.com/bdraco/yalexs-ble/commit/78e00a0615cefb5c22535f1d16eec4681c1229ad))

## v1.8.1 (2022-09-11)
### Fix
* Correct bleak-retry-connector version ([#66](https://github.com/bdraco/yalexs-ble/issues/66)) ([`704b7b1`](https://github.com/bdraco/yalexs-ble/commit/704b7b17c790cc2bf890eff9d9431f45369d4fb2))

## v1.8.0 (2022-09-11)
### Feature
* Implement smart back off ([#65](https://github.com/bdraco/yalexs-ble/issues/65)) ([`a3e9c0a`](https://github.com/bdraco/yalexs-ble/commit/a3e9c0a171a4d9b3da464590f887bd4bc7756f68))

## v1.7.1 (2022-09-10)
### Fix
* Handle dbus already having the lock connected at startup ([#63](https://github.com/bdraco/yalexs-ble/issues/63)) ([`b47b132`](https://github.com/bdraco/yalexs-ble/commit/b47b1320773a15b48ceb3fe2665e4e7b8c19c570))

## v1.7.0 (2022-09-10)
### Feature
* Expose get_device api ([#62](https://github.com/bdraco/yalexs-ble/issues/62)) ([`f49ca9f`](https://github.com/bdraco/yalexs-ble/commit/f49ca9fc58944cc0a971f3cc4912bca126e79637))

## v1.6.4 (2022-08-20)
### Fix
* Raise max attempts to 4 ([#61](https://github.com/bdraco/yalexs-ble/issues/61)) ([`362b664`](https://github.com/bdraco/yalexs-ble/commit/362b6640ea7e76dd18585ad94dd907e13b610da0))

## v1.6.3 (2022-08-20)
### Fix
* Make sure the ble connection is disconnected if the operation is canceled ([#60](https://github.com/bdraco/yalexs-ble/issues/60)) ([`62510ef`](https://github.com/bdraco/yalexs-ble/commit/62510efa6c2d4de9988f4e071984665c8ce3ebfd))

## v1.6.2 (2022-08-20)
### Fix
* Bump bleak-retry-connector ([#59](https://github.com/bdraco/yalexs-ble/issues/59)) ([`309c1d7`](https://github.com/bdraco/yalexs-ble/commit/309c1d7d9d7a27123c3643b4ca2a7fadff95f668))

## v1.6.1 (2022-08-20)
### Fix
* Implement 250ms backoff on dbus error ([#58](https://github.com/bdraco/yalexs-ble/issues/58)) ([`33d9954`](https://github.com/bdraco/yalexs-ble/commit/33d995496f6bf90fba55521fb0769bae2aa317c0))

## v1.6.0 (2022-08-19)
### Feature
* Add support for roaming between adapters while establishing the ble connection ([#56](https://github.com/bdraco/yalexs-ble/issues/56)) ([`a8885a1`](https://github.com/bdraco/yalexs-ble/commit/a8885a1b6038b9cfb272d3cc09d17c0b4f34b33f))

## v1.5.0 (2022-08-19)
### Feature
* Add support for roaming between adapters while establishing the ble connection ([#55](https://github.com/bdraco/yalexs-ble/issues/55)) ([`1a01c74`](https://github.com/bdraco/yalexs-ble/commit/1a01c74c8ceaf5162724ef3f3edf09bce5a3e95f))

## v1.4.0 (2022-08-13)
### Feature
* Add support for the gen2 august locks ([#54](https://github.com/bdraco/yalexs-ble/issues/54)) ([`47fbc46`](https://github.com/bdraco/yalexs-ble/commit/47fbc4613d7e111cc78f51794e818eb018e3c6c0))

## v1.3.2 (2022-08-12)
### Fix
* Bump bleak-retry-connector ([#53](https://github.com/bdraco/yalexs-ble/issues/53)) ([`194ff6b`](https://github.com/bdraco/yalexs-ble/commit/194ff6be8812e5ac8146b43a3d7d07667c437af8))

## v1.3.1 (2022-08-12)
### Fix
* Bleak retry disconnect race fix ([#52](https://github.com/bdraco/yalexs-ble/issues/52)) ([`3e2163c`](https://github.com/bdraco/yalexs-ble/commit/3e2163c66a6193ecad7d80ee557547ec5edcd306))

## v1.2.0 (2022-08-11)
### Feature
* Implement service caching ([#45](https://github.com/bdraco/yalexs-ble/issues/45)) ([`b5ce3ca`](https://github.com/bdraco/yalexs-ble/commit/b5ce3ca4a4e3e088ac1ba19990351facdd8b5186))

## v1.1.3 (2022-08-11)
### Fix
* Battery drain when using dbus-broker ([#49](https://github.com/bdraco/yalexs-ble/issues/49)) ([`7060e0f`](https://github.com/bdraco/yalexs-ble/commit/7060e0f615d6e232383cef6e35ad52799d78e319))

## v1.1.2 (2022-08-10)
### Fix
* Battery drain for locks that broadcast adv of 255 ([#48](https://github.com/bdraco/yalexs-ble/issues/48)) ([`188052b`](https://github.com/bdraco/yalexs-ble/commit/188052bcb4a182420f501ff81a38a45af7de019b))

## v1.1.1 (2022-08-07)
### Fix
* Number of arguments to secure session debug log ([#47](https://github.com/bdraco/yalexs-ble/issues/47)) ([`3a6f211`](https://github.com/bdraco/yalexs-ble/commit/3a6f2117315722df1bbe76d2a91387d3d14b46c4))

## v1.1.0 (2022-08-07)
### Feature
* Improve debug logging ([#46](https://github.com/bdraco/yalexs-ble/issues/46)) ([`526407c`](https://github.com/bdraco/yalexs-ble/commit/526407c215689ef4b8af14931842ef3df3157773))

## v1.0.1 (2022-08-06)
### Fix
* Format strings for debug logging ([#44](https://github.com/bdraco/yalexs-ble/issues/44)) ([`2295773`](https://github.com/bdraco/yalexs-ble/commit/22957735073d7ba60bbbe3c837eab1ec6b667a7b))

## v1.0.0 (2022-08-06)
### Feature
* Add support for gen2 locks ([#43](https://github.com/bdraco/yalexs-ble/issues/43)) ([`40d2b65`](https://github.com/bdraco/yalexs-ble/commit/40d2b652d1e67be352e642ff73c417afaedd61cc))

### Breaking
* The arguments for PushLock are now all keyword. Either a unique local_name or an address must be provided ([`40d2b65`](https://github.com/bdraco/yalexs-ble/commit/40d2b652d1e67be352e642ff73c417afaedd61cc))

## v0.21.0 (2022-08-06)
### Feature
* Tweak debounce to see door close/open faster ([#42](https://github.com/bdraco/yalexs-ble/issues/42)) ([`ee78cdb`](https://github.com/bdraco/yalexs-ble/commit/ee78cdb24779e6f2d210b598d29d2a4b78b425ce))

## v0.20.0 (2022-08-05)
### Feature
* Cancel an update in progress on lock/unlock ([#41](https://github.com/bdraco/yalexs-ble/issues/41)) ([`d1905ae`](https://github.com/bdraco/yalexs-ble/commit/d1905ae2ea75cc47ee794cc413a90727df17774c))

## v0.19.0 (2022-08-05)
### Feature
* Cancel previous lock/unlock requests when a new one comes in ([#40](https://github.com/bdraco/yalexs-ble/issues/40)) ([`4b670d5`](https://github.com/bdraco/yalexs-ble/commit/4b670d53c62bd45f85b0a48f6bd7ac7d62cbbd02))

## v0.18.1 (2022-08-04)
### Fix
* Only validate callback_state if there are callbacks ([#39](https://github.com/bdraco/yalexs-ble/issues/39)) ([`c368456`](https://github.com/bdraco/yalexs-ble/commit/c368456b2cdd855d327e4b984fb2d3a9d4ebc845))

## v0.18.0 (2022-08-04)
### Feature
* Small cleanups ([#38](https://github.com/bdraco/yalexs-ble/issues/38)) ([`26c6c79`](https://github.com/bdraco/yalexs-ble/commit/26c6c795b7fb5c4870d5c9de587361d7b49f75b2))

## v0.17.1 (2022-08-04)
### Fix
* Wrap BleakError as DisconnectedError on disconnect from write ([#37](https://github.com/bdraco/yalexs-ble/issues/37)) ([`30d0a7e`](https://github.com/bdraco/yalexs-ble/commit/30d0a7ef9105ce032949e9fbd4621fb9929861b9))

## v0.17.0 (2022-08-03)
### Feature
* Expose bledevice ([#36](https://github.com/bdraco/yalexs-ble/issues/36)) ([`476abea`](https://github.com/bdraco/yalexs-ble/commit/476abea9393900d5a858b1beb1ef6ba7b9f1bb35))

## v0.16.0 (2022-08-03)
### Feature
* Throw disconnected error if lock disconnects us ([#35](https://github.com/bdraco/yalexs-ble/issues/35)) ([`c1bcf62`](https://github.com/bdraco/yalexs-ble/commit/c1bcf620dbd0270a13a4de79f3dc41aaef28f86d))

## v0.15.1 (2022-08-03)
### Fix
* Do not keep retrying 10x more time if the lock cannot be found ([#34](https://github.com/bdraco/yalexs-ble/issues/34)) ([`704f7bb`](https://github.com/bdraco/yalexs-ble/commit/704f7bb03e40345e6e4c8cae79ae7aeb0b9dc9b8))

## v0.15.0 (2022-08-03)
### Feature
* Add validate function to check creds ([#33](https://github.com/bdraco/yalexs-ble/issues/33)) ([`aadfc76`](https://github.com/bdraco/yalexs-ble/commit/aadfc765618af19b357feab98781c58667a5f8b3))

## v0.14.0 (2022-08-03)
### Feature
* Improve error reporting ([#32](https://github.com/bdraco/yalexs-ble/issues/32)) ([`d81121d`](https://github.com/bdraco/yalexs-ble/commit/d81121dbc367320b2e80db79715536ecc24f1a6c))

## v0.13.0 (2022-08-03)
### Feature
* Tweak update times to improve responsiveness ([`be2278c`](https://github.com/bdraco/yalexs-ble/commit/be2278cf8d75ca23b60f4f0e52345bf24674575b))
* Tweak update times to improve responsiveness ([`b47121c`](https://github.com/bdraco/yalexs-ble/commit/b47121cc1054c001a7e4b7bcc797c6991db95d64))

## v0.12.1 (2022-08-02)
### Fix
* Double update when adv and homekit update at the same time ([#31](https://github.com/bdraco/yalexs-ble/issues/31)) ([`760e429`](https://github.com/bdraco/yalexs-ble/commit/760e42984461ae086599d9fc60395f50d2facffd))

## v0.12.0 (2022-08-02)
### Feature
* Add manual update request ([#30](https://github.com/bdraco/yalexs-ble/issues/30)) ([`26c49a7`](https://github.com/bdraco/yalexs-ble/commit/26c49a7ae7a1ec53c82f4aa20b3c7dcd52a807b6))

## v0.11.0 (2022-08-02)
### Feature
* Speed up first update ([#29](https://github.com/bdraco/yalexs-ble/issues/29)) ([`764894b`](https://github.com/bdraco/yalexs-ble/commit/764894b7400163eefcddf3b846f6365827efa7db))

## v0.10.0 (2022-08-02)
### Feature
* Add connection information ([#28](https://github.com/bdraco/yalexs-ble/issues/28)) ([`36ff430`](https://github.com/bdraco/yalexs-ble/commit/36ff4300f332a8e1a2e1dc37fdfecf6e646fe0b0))

## v0.9.5 (2022-08-02)
### Fix
* Debounced updates ([#27](https://github.com/bdraco/yalexs-ble/issues/27)) ([`a9ce949`](https://github.com/bdraco/yalexs-ble/commit/a9ce949dc8b71992d8d5d5116c227ab5e39597b3))

## v0.9.4 (2022-08-02)
### Fix
* Race in the operation locking ([#26](https://github.com/bdraco/yalexs-ble/issues/26)) ([`ccb3653`](https://github.com/bdraco/yalexs-ble/commit/ccb36530bbd936b875f91579a2e1d661b0c7e13f))

## v0.9.3 (2022-08-02)
### Fix
* Ensure adv updates are processed ([#25](https://github.com/bdraco/yalexs-ble/issues/25)) ([`b655379`](https://github.com/bdraco/yalexs-ble/commit/b655379b93fd6a8b5c54871699f35613c627391c))

## v0.9.2 (2022-08-02)
### Fix
* Schedule race ([#24](https://github.com/bdraco/yalexs-ble/issues/24)) ([`6a5d4cd`](https://github.com/bdraco/yalexs-ble/commit/6a5d4cda45c8286a5b891ef587ff4e0f577a7aaa))

## v0.9.1 (2022-08-02)
### Fix
* Ensure homekit updates take precedence ([#23](https://github.com/bdraco/yalexs-ble/issues/23)) ([`6897092`](https://github.com/bdraco/yalexs-ble/commit/6897092ea6b7a0b5cc8fe1d36e43ed1dda6b37ae))

## v0.9.0 (2022-08-02)
### Feature
* Add lock_info property ([#22](https://github.com/bdraco/yalexs-ble/issues/22)) ([`ac7f956`](https://github.com/bdraco/yalexs-ble/commit/ac7f956cc10753fe1f7e093c95846541912003aa))

## v0.8.0 (2022-08-02)
### Feature
* Add lock info ([#21](https://github.com/bdraco/yalexs-ble/issues/21)) ([`6bd635d`](https://github.com/bdraco/yalexs-ble/commit/6bd635d1d055d86a26534cc0b0c761388b417dac))

## v0.7.1 (2022-08-02)
### Fix
* Defer updates for 10s when there is an update storm ([#20](https://github.com/bdraco/yalexs-ble/issues/20)) ([`142a5c8`](https://github.com/bdraco/yalexs-ble/commit/142a5c8a0f1a2545cccc857c2bbd43779564cafc))

## v0.7.0 (2022-07-28)
### Feature
* Coalesce updates ([#19](https://github.com/bdraco/yalexs-ble/issues/19)) ([`9f5fe74`](https://github.com/bdraco/yalexs-ble/commit/9f5fe74c77d5705d1b6f9e19f4ae177619653895))

## v0.6.1 (2022-07-28)
### Fix
* Handle disconnect race ([#18](https://github.com/bdraco/yalexs-ble/issues/18)) ([`ecd6916`](https://github.com/bdraco/yalexs-ble/commit/ecd691621527144cd1b859090d4182956421e113))

## v0.6.0 (2022-07-28)
### Feature
* Speed up init ([#17](https://github.com/bdraco/yalexs-ble/issues/17)) ([`61f3fbc`](https://github.com/bdraco/yalexs-ble/commit/61f3fbc65bae5386f16e2b1609f7f4666660a6a6))

## v0.5.1 (2022-07-27)
### Fix
* Error handling for d-bus ([#16](https://github.com/bdraco/yalexs-ble/issues/16)) ([`a4c92a0`](https://github.com/bdraco/yalexs-ble/commit/a4c92a056f5ac58877166189a71ffea9fabeac75))

## v0.5.0 (2022-07-27)
### Feature
* Expose lock state ([#15](https://github.com/bdraco/yalexs-ble/issues/15)) ([`2384592`](https://github.com/bdraco/yalexs-ble/commit/2384592dafdc3a9f79a0f98bcdb42b675da403a1))

## v0.4.3 (2022-07-27)
### Fix
* Add dbus error handler ([#14](https://github.com/bdraco/yalexs-ble/issues/14)) ([`2046a95`](https://github.com/bdraco/yalexs-ble/commit/2046a95240c4cf40dfcb923b55b3f9d404698422))

## v0.4.2 (2022-07-27)
### Fix
* Error reporting ([#13](https://github.com/bdraco/yalexs-ble/issues/13)) ([`e7822cf`](https://github.com/bdraco/yalexs-ble/commit/e7822cf483df07b9611a9bab1c4f35b7eb6cc2d8))

## v0.4.1 (2022-07-27)
### Fix
* Cancel lock status update when unlocking/locking ([#12](https://github.com/bdraco/yalexs-ble/issues/12)) ([`1c08fb6`](https://github.com/bdraco/yalexs-ble/commit/1c08fb68ccc360fac7d1c64bd24390819a548db2))

## v0.4.0 (2022-07-27)
### Feature
* Start now return a cancel callable ([#11](https://github.com/bdraco/yalexs-ble/issues/11)) ([`5ff3a36`](https://github.com/bdraco/yalexs-ble/commit/5ff3a36d8a7a0b3720f4ca5022d5bef48f5d712b))

## v0.3.1 (2022-07-27)
### Fix
* Add missing imports ([#10](https://github.com/bdraco/yalexs-ble/issues/10)) ([`4a76d51`](https://github.com/bdraco/yalexs-ble/commit/4a76d5103e8b1d26469847cc7afe1bf7ca9ddaa5))

## v0.3.0 (2022-07-27)
### Feature
* Add serial number helpers ([#9](https://github.com/bdraco/yalexs-ble/issues/9)) ([`3d532dc`](https://github.com/bdraco/yalexs-ble/commit/3d532dc36b0ab53c47762ccdccffb8452c36be75))

## v0.2.0 (2022-07-27)
### Feature
* Change example to use serial number ([#8](https://github.com/bdraco/yalexs-ble/issues/8)) ([`696cd0e`](https://github.com/bdraco/yalexs-ble/commit/696cd0e1d4a9990bf25780e627ebd700c595bf75))

## v0.1.2 (2022-07-27)
### Fix
* Unlock and lock calls without force ([#7](https://github.com/bdraco/yalexs-ble/issues/7)) ([`c660cbb`](https://github.com/bdraco/yalexs-ble/commit/c660cbb0913579fdb4306abaf8c14917e6a458eb))

## v0.1.1 (2022-07-27)
### Fix
* Fix release process ([#6](https://github.com/bdraco/yalexs-ble/issues/6)) ([`551ebc6`](https://github.com/bdraco/yalexs-ble/commit/551ebc6d0f566ddd97d2a4d4cdfd17a943ffabc0))
* Ci ([#5](https://github.com/bdraco/yalexs-ble/issues/5)) ([`9f721c2`](https://github.com/bdraco/yalexs-ble/commit/9f721c254f13c42f077124315bd986067c6c1254))

## v0.1.0 (2022-07-27)
### Feature
* First release ([#4](https://github.com/bdraco/yalexs-ble/issues/4)) ([`234e06d`](https://github.com/bdraco/yalexs-ble/commit/234e06dc3c822cb7219e8dfcd5493989aa8aa2dc))
