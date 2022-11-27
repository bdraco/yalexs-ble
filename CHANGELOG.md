# Changelog

<!--next-version-placeholder-->

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
