# Changelog

<!--next-version-placeholder-->

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
