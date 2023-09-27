import aiohttp


class Deepl:
    BASE_URL = 'https://api-free.deepl.com/v2'

    def __init__(self, api_key, target_lang):
        self.api_key = api_key
        self.target_lang = target_lang

    async def check_translation_limits(self) -> bool:
        url = f'{self.BASE_URL}/usage'
        headers = {'Authorization': f'DeepL-Auth-Key {self.api_key}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    usage_data = await response.json()
                    character_count = usage_data.get("character_count", 0)
                    character_limit = usage_data.get("character_limit", 0)

                    if character_count >= 0.8 * character_limit:
                        return False

        return True

    async def translate(self, text) -> str:
        if len(text) > 10000:
            return 'Text too long'

        limits_ok = await self.check_translation_limits()
        if not limits_ok:
            return 'Limit reached'

        params = {
            "auth_key": self.api_key,
            "text": text,
            "source_lang": "PL",
            "target_lang": self.target_lang,
        }

        url = f'{self.BASE_URL}/translate'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    translated_text = response_data["translations"][0]["text"]
                    return translated_text
                else:
                    return f"Translation error: {response.status}"
