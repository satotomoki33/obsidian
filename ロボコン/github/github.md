## レポジトリ　作り方

ディレクトリの中で`git init`

.gitignore のファイルを作る

中身は

```Cmake
CMakeLists.txt.user
CMakeCache.txt
CMakeFiles
CMakeScripts
Testing
Makefile
cmake_install.cmake
install_manifest.txt
compile_commands.json
CTestTestfile.cmake
_deps
CMakeUserPresets.json

build/

```

自分のgit hubのページからNew repository で新しいレポジトリを作る

git remote add…のコマンドをターミナルで入力し、紐付ける

git add . で変更したファイルをステージ上に上げる

git commit -m “コミット名”　でコミットする

git push origin master でマスターにつなげる

ブランチで作業してるときにマスターの変更をブランチに取り込む: git merge master

### git diff 差分が見れる

ctrl + z で終了できる
```
sato@sato-PC-GN20CBDDS:~/robocon/gittest$ git diff  
diff --git a/yyy b/yyy  
index 88fac34..ca531a3 100644  
--- a/yyy  
+++ b/yyy  
@@ -1 +1 @@  
-hiih  
+hhhhhhhhhhhhhhhhiih
```

## git branch
```
sato@sato-PC-GN20CBDDS:~/robocon/gittest$ git branch --list  
main  
unko

unti  
sato@sato-PC-GN20CBDDS:~/robocon/gittest$
```

### git pull

**git pull** とは、さきほど説明した**git fetch** と **git merge** をいっぺんに実行するコマンドのことです。

**git merge** のセクションで言っていた以下のコマンド。

```bash
git fetch // 先にリモートの状態をリモート追跡ブランチにコピー
git merge origin/master // リモートのコピーからマージ
```

こちらのコマンドは、

```bash
git pull origin master
```

とイコールです。フェッチしてからマージするのMENDOIと思うようになったら使いどきです。

## git pull --rebase とは

ついにお待ちかねの **git pull --rebase** です。

- **-rebase** は **git pull** コマンドのオプションです。**git pull** は **fetch** + **merge** ですが、**--rebase** オプションをつけると **fetch** + **rebase**として実行します。

```bash
git pull --rebase origin main
```

サブモジュールもstashしておく

サブモジュールがコンフリクトしたら

```bash
cd src/common/abu2026-mech-source
git fetch origin  # 最新のコミット情報を取得
git checkout 35fde06
```

そのサブモジュールをaddしてgit rebase —continue

`git config --global core.editor code`

[リベースの後の操作](https://app.notion.com/p/2cc9a48d8ee88089bfb1f7f7b524d7dc?pvs=21)

注意

git pull --rebaseは他の人のライブラリの修正とかそういうのした時にやるとコンフリクトもなくて楽

したあとは、無理やりプッシュのやつやれば行ける

違う端末でプルするときは、**自分の方で変更してない最初の時**。ラテパンとかのときは

フェッチしてから

```bash
git reset --hard origin/自分のブランチ
```

[コミットを消したい](https://app.notion.com/p/17b9a48d8ee8803aa454f661e4f60915?pvs=21)

[git のリモートレポジトリを解除したい](https://app.notion.com/p/git-1859a48d8ee8805aac53ce3618eddb69?pvs=21)

[https://qiita.com/k_yamashita/items/040c04f8798d2384806e](https://qiita.com/k_yamashita/items/040c04f8798d2384806e)

### git stash

[【git stash】コミットはせずに変更を退避したいとき - Qiita](https://qiita.com/chihiro/items/f373873d5c2dfbd03250)

### リモートにプッシュしてしまったコミットを消す

ローカルのコミットをリモートのブランチに無理やりプッシュする

```bash
git push origin <ローカルブランチ名> --force-with-lease
```

サブモジュールのアップデート（とりあえずこれでいい）

```bash
git submodule update --init --recursive
```

[みんなamendとfixupを覚えよう](https://app.notion.com/p/amend-fixup-2f99a48d8ee8809bbaf5d8ad58560d39?pvs=21)