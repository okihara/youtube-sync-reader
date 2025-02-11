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
            # 入力データをJSON文字列に変換
            input_json = json.dumps(subtitles, ensure_ascii=False)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
入力された字幕データの"text"フィールドを日本語に翻訳してください。
時間情報（start, duration）はそのまま保持してください。
入力と同じJSON配列形式で返してください：
[
    {
        "start": 開始時間（秒）,
        "duration": 継続時間（秒）,
        "text": "翻訳されたテキスト"
    },
    ...
]
"""},
                    {"role": "user", "content": input_json}
                ],
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                if isinstance(result, list):
                    return result
                else:
                    raise TranslationError("予期しないJSONフォーマット")
            except json.JSONDecodeError as e:
                raise TranslationError(f"JSONのパースに失敗しました: {response.choices[0].message.content}")
                
        except Exception as e:
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
