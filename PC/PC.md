**その買い方が一番おすすめ。**  
一気に高性能PCを完成させるのではなく、

> **最初はGPUなしで動く自作デスクトップを作る → 必要になった順にGPU・SSD・メモリを追加**

という構成にすると、ミニPC＋OCuLinkより拡張しやすく、最終的な総額も抑えやすい。

## 最初に作る構成

現時点では、次のような**AM5ベース**がよさそう。

|部品|最初の構成|
|---|---|
|CPU|**Ryzen 5 8600G**|
|CPUクーラー|付属クーラー|
|マザーボード|B650・メモリ4スロット・M.2が2本以上|
|メモリ|できれば32GB（16GB×2）|
|SSD|NVMe 1TB|
|電源|650W～750W、ATX 3.x、80 PLUS Gold|
|ケース|microATXまたはATX|
|GPU|最初は付けない|
|OS|Ubuntu 24.04|

Ryzen 5 8600Gは6コア12スレッドで、普通のCPUより強い内蔵GPU「Radeon 760M」を搭載している。GPUを買わなくても画面出力だけでなく、軽めのGazebo・Webots・RVizから始められる。([AMD](https://www.amd.com/en/products/processors/desktops/ryzen/8000-series/amd-ryzen-5-8600g.html "AMD Ryzen™ 5 8600G Desktop Processor"))

最初の予算は、相場によるけど**だいたい9万～13万円前後**を目安にするといい。B650マザーボードは、現在1万5,000円前後から3万円弱の製品が見つかる。([kakaku.com](https://kakaku.com/pc/motherboard/itemlist.aspx?pdf_Spec116=16&pdf_ma=53 "価格.com - チップセット(AMD):B650 MSI(エムエスアイ)のマザーボード 比較 2026年人気売れ筋ランキング"))

## 段階的に追加する

### 第1段階：GPUなし

まずは以下を動かす。

- ROS 2の開発
    
- VS Code・DevContainer
    
- RViz
    
- Webots
    
- 軽めのGazebo
    
- 実機用ROSノードのビルド
    
- カメラ画像の確認
    

内蔵GPUなので重い3Dシミュレーションは厳しいけど、勉強・開発・軽い動作確認には使える。

### 第2段階：GPUを追加

お金ができたら、PCIeスロットに普通のデスクトップGPUを挿す。

候補は用途別に、

|GPU|向いている用途|
|---|---|
|中古RTX 3060 12GB|安くCUDA・画像処理も始めたい|
|RTX 4060|省電力重視|
|RTX 5060|新品で長く使いたい|
|RTX 5060 Ti|重めのGazeboや画像処理にも余裕|
|RTX 5070以上|Isaac Simなども視野に入れる|

ROS・Gazebo中心なら、最初はRTX 3060～5060クラスで十分。GPUを追加した時点で、かなり本格的なシミュレーションPCになる。

## 第3段階：SSDとメモリを追加

次に必要になったら、

- SSDをもう1TB～2TB追加
    
- メモリを64GBへ
    
- CPUクーラーを大型化
    
- ケースファンを追加
    

という順で強化できる。

特にROSワークスペース、Dockerイメージ、ログ、シミュレータを入れるとSSDを使うので、**マザーボードのM.2スロットが2本以上あること**は確認した方がいい。

## 最初から妥協しない方がいい部品

あとから簡単に追加できるのは、

- GPU
    
- SSD
    
- ケースファン
    

逆に、最初から少し良いものにした方がいいのは、

- **マザーボード**
    
- **電源**
    
- **ケース**
    

ここを安さだけで選ぶと、将来GPUが入らない、電源容量が足りない、SSDを増設できない、ということになりやすい。

### マザーボード

次を満たすB650を選ぶ。

- メモリスロット4本
    
- M.2スロット2本以上
    
- PCIe x16スロット
    
- BIOS Flashback
    
- 2.5GbE
    
- 必要ならWi-Fi・Bluetooth
    

AM5はAMDが**2029年までサポートを継続する**と発表しているため、将来CPUだけ新しいRyzenへ交換できる可能性が高い。段階的な自作PCとかなり相性がいい。([AMD](https://www.amd.com/en/blogs/2026/amd-computex-2026-10-years-of-am4-am5-support-through.html "AMD Computex 2026: 10 Years of AM4, AM5 Support Through 2029 and Expanded RDNA 4 Gaming"))

### 電源

GPUなしの状態では500Wでも動くけど、買い直しを避けるなら、

> **650W Gold：RTX 5060クラスまで想定**  
> **750W Gold：もう少し上のGPUも想定**

がおすすめ。

2026年7月現在、650W電源は安いBronze製品なら約6,000円、ATX 3対応のGold製品なら約1万6,000円の掲載例がある。ここは約1万円余分に出しても、信頼できる製品を選ぶ価値がある。([Yahoo!ショッピング](https://shopping.yahoo.co.jp/searchranking/pc%2B%E9%9B%BB%E6%BA%90%E3%83%A6%E3%83%8B%E3%83%83%E3%83%88%2B650w/0/ "〖2026年7月〗pc+電源ユニット+650wのおすすめ人気ランキング - Yahoo!ショッピング"))

## 8600Gの注意点

Ryzen 5 8600Gには一つ注意点がある。

通常のRyzen 7000・9000シリーズではGPUスロットをPCIe x16で利用できることが多いが、8600Gなどの8000Gシリーズでは、マザーボードによって**PCIe 4.0 x8接続**になる。MSIのB650マザーボード仕様にも、7000・9000シリーズはx16、8600Gなどはx8と記載されている。([MSI Japan](https://jp.msi.com/Motherboard/B650M-GAMING-PLUS-WIFI/Specification "B650M GAMING PLUS WIFI"))

RTX 3060～5060程度なら大きな問題になりにくいけど、将来かなり高性能なGPUを付けるなら少しもったいない。

そのため、選び方は二つ。

### 今すぐGPUなしでシミュレーションしたい

> **Ryzen 5 8600G**

内蔵GPUが強いので、段階購入と相性がいい。

### 最終的なGPU性能を優先したい

> **Ryzen 5 7600＋安い中古GPU、またはGPUを買うまで軽作業だけする**

Ryzen 5 7600にも画面出力用の内蔵Radeon Graphicsがあり、PCIe 5.0と24本の使用可能なPCIeレーンを備えている。ただし内蔵GPUは8600Gよりかなり小さく、本格的な3Dシミュレーション用ではない。([AMD](https://www.amd.com/en/products/processors/desktops/ryzen/7000-series/amd-ryzen-5-7600.html?utm_source=chatgpt.com "AMD Ryzen™ 5 7600"))

## 俺ならこの順番にする

```text
第1段階：約10万円前後
Ryzen 5 8600G
B650マザーボード
RAM 32GB
SSD 1TB
650Wまたは750W電源
ケース

        ↓

第2段階
NVIDIA GPUを追加

        ↓

第3段階
SSD追加
RAM 64GB化

        ↓

第4段階
必要ならCPUを将来の8コアRyzenへ交換
```

この方法なら、最初からGPU込みの20万円近いPCを買わなくても、**まず普通に使えるPCを完成させて、あとからシミュレーション性能を伸ばせる**。

持ち運ばないなら、OCuLinkミニPCよりこの自作デスクトップ方式の方が、ともきの用途には合っていると思う。OCuLink用ドックやGPU用外部電源を別に買わなくてよく、CPUまで交換できるのが大きい。

候補パーツが決まったら、値下がりしたときだけ知らせる価格監視も設定する？