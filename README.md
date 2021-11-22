# API для системы опроса
## Деплой
```
git clone https://github.com/itiligator/fab.git

docker build -t fab .

docker run -d -p 8080:8080 fab
```
## Документация
Документацию смотри по адресам `/swagger/` или `/redoc/`

### Дополнительно
- получение активных опросов: `/surveys/?active=1`
- логин: `/api-auth/login/`. Админ: пользователь `a`, пароль `1`
- стандартная админка: `/admin/`
- Типы вопросов: `0` - с текстовым ответом, `1` - с выбором одного варианта, `2` - с выбором нескольких вариантов

### Пример запроса для прохождения опроса
POST на `/submissions/` с вот таким payload:
```
{
	"data": [{
			"question": 1,
			"text": "Андрюша, 30 годиков"
		},
		{
			"question": 2,
			"selections": [1]
		},
		{
			"question": 4,
			"selections": [6, 7]
		}
	],
	"survey": 1,
	"user": 1
}
```