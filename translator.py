import json
import openai
from typing import List, Dict, Optional

class TranslationError(Exception):
    """翻訳処理中のエラーを表すカスタム例外"""
    pass

class Translator:
    def __init__(self, api_key: Optional[str] = None):
        """
        Translatorクラスの初期化
        Args:
            api_key: OpenAI APIキー（省略時は環境変数から読み込み）
        """
        if api_key:
            openai.api_key = api_key
        self.client = openai.OpenAI()

    def _chunk_subtitles(self, subtitles: List[Dict], chunk_size: int = 50) -> List[List[Dict]]:
        """
        字幕データを指定されたサイズのチャンクに分割する
        Args:
            subtitles: 分割する字幕データのリスト
            chunk_size: 1チャンクあたりの字幕数
        Returns:
            分割された字幕データのリスト
        """
        return [subtitles[i:i + chunk_size] for i in range(0, len(subtitles), chunk_size)]

    def translate_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
        """
        字幕データを翻訳する
        Args:
            subtitles: 翻訳する字幕データのリスト
        Returns:
            翻訳された字幕データのリスト
        Raises:
            TranslationError: 翻訳処理中にエラーが発生した場合
        """
        try:
            print("[INFO] 翻訳処理を開始します")
            
            # 字幕データをチャンクに分割
            chunks = self._chunk_subtitles(subtitles)
            print(f"[INFO] 字幕データを {len(chunks)} チャンクに分割しました（1チャンク {len(chunks[0])} 件）")
            translated_chunks = []
            
            # チャンクごとに翻訳
            for i, chunk in enumerate(chunks, 1):
                print(f"[INFO] チャンク {i}/{len(chunks)} を処理中... ({len(chunk)} 件)")
                print(f"[DEBUG] チャンク {i} の最初の字幕: {chunk[0]}")
                
                # 入力データをJSON文字列に変換
                input_json = json.dumps(chunk, ensure_ascii=False)
                print(f"[DEBUG] チャンク {i} のトークン数を計算中...")
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": """
入力された字幕データの"text"フィールドを日本語に翻訳してください。
時間情報（start, duration）は入力の数値をそのまま保持してください。
入力と同じJSON配列形式で返してください。
例：
[
    {
        "start": 1.5,
        "duration": 2.0,
        "text": "翻訳されたテキスト"
    }
]
"""},
                        {"role": "user", "content": input_json}
                    ],
                )
                
                try:
                    response_content = response.choices[0].message.content.strip()
                    # 文字列がクォートで囲まれている場合は除去
                    if response_content.startswith('"') and response_content.endswith('"'):
                        response_content = response_content[1:-1]
                    # エスケープされた文字列を元に戻す
                    response_content = response_content.encode().decode('unicode_escape')
                    result = json.loads(response_content)
                    
                    if isinstance(result, list):
                        print(f"[INFO] チャンク {i} の翻訳が完了しました")
                        print(f"[DEBUG] チャンク {i} の最初の翻訳結果: {result[0]}")
                        translated_chunks.extend(result)
                    else:
                        raise TranslationError(f"チャンク {i} で予期しないJSONフォーマット")
                except json.JSONDecodeError as e:
                    raise TranslationError(f"チャンク {i} でJSONのパースに失敗しました: {response.choices[0].message.content}")
            
            print(f"[INFO] 全ての翻訳が完了しました（合計 {len(translated_chunks)} 件）")
            return translated_chunks
                
        except Exception as e:
            print(f"[ERROR] 翻訳に失敗しました: {str(e)}")
            import traceback
            print(f"[DEBUG] スタックトレース:\n{traceback.format_exc()}")
            raise TranslationError(f"翻訳に失敗しました: {str(e)}")

if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample_subtitles = [
        {
            "start": 0,
            "duration": 5,
            "text": "Hello, this is a test subtitle."
        },
        {
            "start": 5,
            "duration": 3,
            "text": "Let's try translation."
        }
    ]
    
    try:
        translator = Translator()
        result = translator.translate_subtitles(sample_subtitles)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except TranslationError as e:
        print(f"エラー: {e}")
