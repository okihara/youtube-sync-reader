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

    def _chunk_subtitles(self, subtitles: List[Dict], chunk_size: int = 25) -> List[List[Dict]]:
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

    def _split_by_punctuation(self, text: str) -> List[str]:
        """
        テキストを句読点で分割する
        Args:
            text (str): 分割するテキスト
        Returns:
            List[str]: 分割されたテキストのリスト
        """
        # まず句点で分割
        sentences = []
        for sentence in text.split('。'):
            if not sentence.strip():
                continue
            # 読点で分割
            parts = [p.strip() for p in sentence.split('、')]
            # 空の部分を除去し、読点を付け直す
            parts = [(p + '、') for p in parts if p]
            if parts:
                # 最後の部分は句点にする
                parts[-1] = parts[-1].rstrip('、') + '。'
                sentences.extend(parts)
        return sentences

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
                try:
                    print(f"[INFO] チャンク {i}/{len(chunks)} を処理中... ({len(chunk)} 件)")
                    
                    # チャンク内のテキストを連結
                    texts = []
                    for item in chunk:
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
できるだけ自然な日本語になるように翻訳してください。
"""},
                            {"role": "user", "content": combined_text}
                        ]
                    )
                    
                    # 翻訳結果を句読点で分割
                    translated_text = response.choices[0].message.content.strip()
                    translated_parts = self._split_by_punctuation(translated_text)
                    
                    # 分割した部分を元のチャンクの数に合わせて調整
                    if len(translated_parts) > len(chunk):
                        # 多すぎる場合は、均等に結合
                        parts_per_chunk = len(translated_parts) / len(chunk)
                        adjusted_parts = []
                        current_parts = []
                        
                        for j, part in enumerate(translated_parts):
                            current_parts.append(part)
                            if (j + 1) / parts_per_chunk >= len(adjusted_parts) + 1:
                                adjusted_parts.append(''.join(current_parts))
                                current_parts = []
                        
                        if current_parts:
                            adjusted_parts.append(''.join(current_parts))
                        
                        translated_parts = adjusted_parts[:len(chunk)]
                    elif len(translated_parts) < len(chunk):
                        # 少なすぎる場合は空文字で補完
                        translated_parts.extend([''] * (len(chunk) - len(translated_parts)))
                    
                    # 翻訳結果を元のタイミング情報と組み合わせる
                    for j, (item, translated) in enumerate(zip(chunk, translated_parts)):
                        translated_item = {
                            'start': item['start'],
                            'duration': item['duration'],
                            'text': translated if translated else ''
                        }
                        translated_chunks.append(translated_item)
                    
                    print(f"[INFO] チャンク {i} の翻訳が完了しました")
                    print(f"[DEBUG] チャンク {i} の最初の翻訳結果: {translated_chunks[-len(chunk)]}")
                    
                except Exception as e:
                    print(f"Translation error: {e}")
                    # エラーの場合は原文をそのまま使用
                    translated_chunks.extend(chunk)
            
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
