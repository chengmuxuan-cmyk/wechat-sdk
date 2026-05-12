# WeChat_SDK 鍙紨杩涙灦鏋勯噸鏋勮鍒?
## Summary

灏嗗綋鍓嶉」鐩噸鏋勪负姝ｅ紡 SDK锛氬睍绀哄悕 `WeChat_SDK`锛屽彂甯冨寘鍚?`wechat-sdk`锛屽鍏ュ寘鍚?`wechat_sdk`銆?
鏋舵瀯涓荤嚎锛?
```text
鑳藉姏鍗忚 Capability
  鈫?閫氱敤鎿嶄綔姝ラ Pipeline
  鈫?瀹㈡埛绔?Profile YAML
  鈫?鐗堟湰宸紓 Selector / Pipeline Override
  鈫?WeChatClient 缁熶竴鎺ュ彛
```

鏈潵鏂扮増鏈紭鍏堟柊澧為厤缃拰灏戦噺 override锛屼笉閲嶆瀯鍏叡鎺ュ彛鍜屾牳蹇冩湇鍔°€?
## Core Design

- 鎵€鏈夊姛鑳戒互 capability 涓轰腑蹇冿紝鑰屼笉鏄互鐗堟湰绫讳负涓績銆?- `clients.yaml` 鎻忚堪绐楀彛鎸囩汗銆佽繘绋嬪悕銆佺増鏈寖鍥村拰 selector 鏂囦欢銆?- `capabilities.yaml` 璁板綍 3.9 鎶€鑳芥爲銆?.x 鏀寔鐘舵€併€侀粯璁や氦浜掓ā寮忓拰 pipeline銆?- `pipelines.yaml` 瀹氫箟閫氱敤姝ラ锛屼笉鍚岀増鏈彧鍦ㄥ繀瑕佹椂 override銆?- 榛樿 `mode="auto"`锛氬悗鍙颁紭鍏堬紝澶辫触鍞ら啋寰俊鍓嶅彴閲嶈瘯銆?- SDK 鎻愪緵鐩戝惉浜嬩欢妯″瀷锛屼絾鑷姩鍥炲鍐崇瓥鏀惧湪涓氬姟灞傘€?
## 3.9 鎶€鑳芥爲鍩虹嚎

鑳藉姏鍩燂細

- 瀹㈡埛绔笌绐楀彛锛氭娴嬨€佷俊鎭€佽瘖鏂€佺櫥褰曘€佷簩缁寸爜銆佸瀹㈡埛绔€?- 浼氳瘽涓庡鑸細褰撳墠鑱婂ぉ銆佷細璇濆垪琛ㄣ€佸垏鎹㈣亰澶┿€佺嫭绔嬬獥鍙ｃ€?- 娑堟伅鍙戦€侊細鏂囨湰銆佹枃浠躲€侀摼鎺ュ崱鐗囥€佽〃鎯呫€佽闊炽€丂銆?- 娑堟伅璇诲彇涓庣洃鍚細鍏ㄩ儴娑堟伅銆佹柊娑堟伅銆佸巻鍙叉秷鎭€佺洃鍚簨浠躲€佸洖璋冩淳鍙戙€?- 娑堟伅瀵硅薄锛氬紩鐢ㄣ€佽浆鍙戙€佸垹闄ゃ€佸閫夈€佸彂閫佽€呰鎯呫€佸姞濂藉弸銆?- 娑堟伅绫诲瀷锛氭枃鏈€佸浘鐗囥€佽棰戙€佽闊炽€佹枃浠躲€侀摼鎺ャ€佸紩鐢ㄣ€佸悎骞躲€佺瑪璁扮瓑銆?- 鑱旂郴浜猴細濂藉弸璇︽儏銆佹悳绱€佹柊鏈嬪弸銆佸娉ㄣ€佹爣绛俱€佸姞濂藉弸銆?- 缇よ亰锛氬缓缇ゃ€佹媺浜恒€佺Щ闄ゃ€佺兢鍚嶃€佸叕鍛娿€佺兢澶囨敞銆佺兢鏄电О銆?- 鏂囦欢绠＄悊锛氬彂閫併€佷笅杞姐€佽亰澶╂枃浠剁鐞嗗櫒銆?- 鍥剧墖涓?OCR锛氶瑙堛€佷繚瀛樸€丱CR銆佷笂涓€寮犮€佷笅涓€寮犮€?- 寮圭獥锛氳幏鍙栥€佺‘璁ゃ€佸彇娑堛€佹枃鏈彁鍙栥€?- 鏈嬪弸鍦堬細鎵撳紑銆佽鍙栥€佺偣璧炪€佽瘎璁恒€佸彂甯冦€佷繚瀛樺浘鐗囥€?
## Package Structure

```text
wechat_sdk/
  client.py
  errors.py
  params.py
  logging.py
  core/
  services/
  msgs/
  config/
```

`wxauto/` is deprecated reference code and is not part of the new SDK package.
## Test Plan

```powershell
uv sync
uv run python -m compileall wechat_sdk examples
uv run python examples\diagnose.py
uv run python examples\smoke.py
```

瀹夊叏瑕佹眰锛?
- 鐩爣涓嶅瓨鍦ㄤ笉寰楄鍙戝綋鍓嶈亰澶┿€?- 鏂囦欢涓嶅瓨鍦ㄦ姏鏄庣‘寮傚父銆?- 鍓创鏉垮け璐ユ姏 `ClipboardError`銆?- 鎺т欢涓嶅瓨鍦ㄦ姏 `ControlNotFoundError`銆?- 涓嶆敮鎸佺増鏈姏 `UnsupportedWeChatVersionError`銆?- capability 鏈疄鐜版姏 `CapabilityNotSupportedError`銆?
