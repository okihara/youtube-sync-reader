import json
import os
import openai
import hashlib
from typing import List, Dict, Optional, Tuple

class TranslationError(Exception):
    """翻訳処理中のエラーを表すカスタム例外"""
    pass

class Translator:
    # クラス定数
    DEFAULT_CHUNK_SIZE = 25
    DEFAULT_MODEL = "gpt-4o"
    SYSTEM_PROMPT = """
英語のテキストを日本語に翻訳してください。
入力は複数の文が連結されています。
各文はピリオドで区切られています。
できるだけ自然な日本語になるように翻訳してください。
"""
    TRANSLATION_DIR = "subtitles/translations"

    def __init__(self, api_key: Optional[str] = None, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Translatorクラスの初期化
        Args:
            api_key: OpenAI APIキー（省略時は環境変数から読み込み）
            chunk_size: 1チャンクあたりの字幕数
        """
        if api_key:
            openai.api_key = api_key
        self.client = openai.OpenAI()
        self.chunk_size = chunk_size
        os.makedirs(self.TRANSLATION_DIR, exist_ok=True)

    def _get_chunk_hash(self, chunk: List[Dict]) -> str:
        """
        チャンクの内容からハッシュを生成する
        Args:
            chunk: ハッシュを生成する字幕チャンク
        Returns:
            チャンクのハッシュ値
        """
        chunk_text = json.dumps([item['text'] for item in chunk], sort_keys=True)
        return hashlib.md5(chunk_text.encode()).hexdigest()

    def _get_translation_path(self, chunk_hash: str) -> str:
        """
        翻訳ファイルのパスを取得する
        Args:
            chunk_hash: チャンクのハッシュ値
        Returns:
            翻訳ファイルのパス
        """
        return os.path.join(self.TRANSLATION_DIR, f"{chunk_hash}.txt")

    def _load_translation(self, chunk_hash: str) -> Optional[List[str]]:
        """
        保存済みの翻訳を読み込む
        Args:
            chunk_hash: チャンクのハッシュ値
        Returns:
            翻訳テキストのリスト、存在しない場合はNone
        """
        translation_path = self._get_translation_path(chunk_hash)
        if os.path.exists(translation_path):
            with open(translation_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        return None

    def _save_translation(self, chunk_hash: str, translations: List[str]) -> None:
        """
        翻訳をファイルに保存する
        Args:
            chunk_hash: チャンクのハッシュ値
            translations: 翻訳テキストのリスト
        """
        translation_path = self._get_translation_path(chunk_hash)
        with open(translation_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(translations))

    def _chunk_subtitles(self, subtitles: List[Dict]) -> List[List[Dict]]:
        """
        字幕データを指定されたサイズのチャンクに分割する
        Args:
            subtitles: 分割する字幕データのリスト
        Returns:
            分割された字幕データのリスト
        """
        return [subtitles[i:i + self.chunk_size] for i in range(0, len(subtitles), self.chunk_size)]

    def _split_by_punctuation(self, text: str) -> List[str]:
        """
        テキストを句読点で分割する
        Args:
            text: 分割するテキスト
        Returns:
            分割されたテキストのリスト
        """
        sentences = []
        for sentence in text.split('。'):
            if not sentence.strip():
                continue
            parts = [p.strip() for p in sentence.split('、')]
            parts = [(p + '、') for p in parts if p]
            if parts:
                parts[-1] = parts[-1].rstrip('、') + '。'
                sentences.extend(parts)
        return sentences

    def _prepare_chunk_text(self, chunk: List[Dict]) -> str:
        """
        チャンクのテキストを翻訳用に準備する
        Args:
            chunk: 準備する字幕チャンク
        Returns:
            連結されたテキスト
        """
        texts = []
        for item in chunk:
            text = item['text'].strip()
            if not text.endswith('.'):
                text += '.'
            texts.append(text)
        return ' '.join(texts)

    def _translate_text(self, text: str) -> str:
        """
        テキストを翻訳する
        Args:
            text: 翻訳するテキスト
        Returns:
            翻訳されたテキスト
        Raises:
            TranslationError: 翻訳APIでエラーが発生した場合
        """
        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise TranslationError(f"翻訳APIエラー: {str(e)}")

    def _adjust_translated_parts(self, translated_parts: List[str], chunk_size: int) -> List[str]:
        """
        翻訳結果を元のチャンクサイズに調整する
        Args:
            translated_parts: 調整する翻訳パーツ
            chunk_size: 目標のチャンクサイズ
        Returns:
            調整された翻訳パーツ
        """
        if len(translated_parts) > chunk_size:
            parts_per_chunk = len(translated_parts) / chunk_size
            adjusted_parts = []
            current_parts = []
            
            for i, part in enumerate(translated_parts):
                current_parts.append(part)
                if (i + 1) / parts_per_chunk >= len(adjusted_parts) + 1:
                    adjusted_parts.append(''.join(current_parts))
                    current_parts = []
            
            if current_parts:
                adjusted_parts.append(''.join(current_parts))
            
            return adjusted_parts[:chunk_size]
        elif len(translated_parts) < chunk_size:
            return translated_parts + [''] * (chunk_size - len(translated_parts))
        return translated_parts

    def _process_chunk(self, chunk: List[Dict]) -> List[str]:
        """
        1つのチャンクを処理する
        Args:
            chunk: 処理する字幕チャンク
        Returns:
            翻訳されたテキストのリスト
        """
        try:
            chunk_hash = self._get_chunk_hash(chunk)
            cached_translation = self._load_translation(chunk_hash)
            
            if cached_translation:
                print(f"[INFO] キャッシュされた翻訳を使用します")
                return cached_translation
            
            combined_text = self._prepare_chunk_text(chunk)
            translated_text = self._translate_text(combined_text)
            translated_parts = self._split_by_punctuation(translated_text)
            adjusted_parts = self._adjust_translated_parts(translated_parts, len(chunk))
            
            self._save_translation(chunk_hash, adjusted_parts)
            return adjusted_parts
            
        except Exception as e:
            print(f"チャンク処理エラー: {e}")
            return [''] * len(chunk)

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
            chunks = self._chunk_subtitles(subtitles)
            print(f"[INFO] 字幕データを {len(chunks)} チャンクに分割しました（1チャンク {len(chunks[0])} 件）")
            
            translated_subtitles = []
            for i, chunk in enumerate(chunks, 1):
                print(f"[INFO] チャンク {i}/{len(chunks)} を処理中... ({len(chunk)} 件)")
                translated_texts = self._process_chunk(chunk)
                
                # 翻訳テキストと元のタイミング情報を組み合わせる
                for item, translated_text in zip(chunk, translated_texts):
                    translated_subtitles.append({
                        'start': item['start'],
                        'duration': item['duration'],
                        'text': translated_text
                    })
                
                print(f"[INFO] チャンク {i} の翻訳が完了しました")
            
            print(f"[INFO] 全ての翻訳が完了しました（合計 {len(translated_subtitles)} 件）")
            return translated_subtitles
                
        except Exception as e:
            raise TranslationError(f"翻訳処理エラー: {str(e)}")

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
        print(f"エラーが発生しました: {e}")
