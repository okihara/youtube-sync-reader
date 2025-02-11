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

    def _chunk_subtitles(self, subtitles: List[Dict], chunk_size: int = 100) -> List[List[Dict]]:
        """
        字幕データを指定されたサイズのチャンクに分割する
        Args:
            subtitles: 分割する字幕データのリスト
            chunk_size: 1チャンクあたりの字幕数
        Returns:
            分割された字幕データのリスト
        """
        chunks = []
        for i in range(0, len(subtitles), chunk_size):
            chunks.append(subtitles[i:i + chunk_size])
        return chunks

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
                
                # チャンク内のテキストを連結
                texts = []
                for item in chunk:
                    # 文の区切りを明確にするためにピリオドを追加
                    text = item['text'].strip()
                    if not text.endswith('.'):
                        text += '.'
                    texts.append(text)
                
                combined_text = ' '.join(texts)
                print(f"[DEBUG] チャンク {i} の連結テキスト: {combined_text[:100]}...")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """
英語のテキストを日本語に翻訳してください。
入力は複数の文が連結されています。
各文はピリオドで区切られています。
翻訳結果も同じ数の文に分かれるようにしてください。
"""},
                        {"role": "user", "content": combined_text}
                    ]
                )
                
                # 翻訳結果を文単位で分割
                translated_text = response.choices[0].message.content.strip()
                translated_sentences = [s.strip() for s in translated_text.split('。') if s.strip()]
                
                if len(translated_sentences) != len(chunk):
                    print(f"[WARN] チャンク {i} の文の数が一致しません: 元={len(chunk)}, 翻訳後={len(translated_sentences)}")
                    # 数が合わない場合は、元の数に合わせて調整
                    if len(translated_sentences) > len(chunk):
                        translated_sentences = translated_sentences[:len(chunk)]
                    else:
                        # 足りない分は空文字で補完
                        translated_sentences.extend([''] * (len(chunk) - len(translated_sentences)))
                
                # 翻訳結果を元のタイミング情報と組み合わせる
                for j, (item, translated) in enumerate(zip(chunk, translated_sentences)):
                    translated_item = {
                        'start': item['start'],
                        'duration': item['duration'],
                        'text': translated + ('。' if translated else '')
                    }
                    translated_chunks.append(translated_item)
                
                print(f"[INFO] チャンク {i} の翻訳が完了しました")
                print(f"[DEBUG] チャンク {i} の最初の翻訳結果: {translated_chunks[-len(chunk)]}")
            
            print(f"[INFO] 全ての翻訳が完了しました（合計 {len(translated_chunks)} 件）")
            return translated_chunks
                
        except Exception as e:
            raise TranslationError(str(e))

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
