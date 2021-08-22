# Simple Telegram Bot

## Setup

### Anaconda Setup

You will need to have Anaconda installed.

```bash
conda create -n simple_bot python=3.8 numpy pandas -y
conda activate simple_bot
pip install pyTelegramBotAPI
pip install python-telegram-bot-calendar
```

### Telegram Setup

Obtain an API key from Telegram @botfather, then add a file `config/secret.py` with the following lines:

```python
TELEGRAM_KEY = "<YOUR_TELEGRAM_KEY>"
```

### Start the Bot

```bash
python main.py
```

## Services (Concept)

A `Service` is defined as a unit of functionality. It can be triggered by multiple commands.

The program maintains a dictionary that maps from user ID (`User.id_`) to its active service (`Service`). Every active service instance contains a data cache `Service.data` that will be available across multiple messages.

**When a command is entered**:

- A new `Service` instance is created for the user, depending on the command. (Unknown commands are currently mapped to `/help`)
- `Service.setup` is called, which replies to the user and waits for:
  1.  a user message
  2.  a callback query

**When a message is entered**:

- The active `Service` instance for the user is fetched
- `Service.next` is called, which replies to the user and waits for:
  1.  a user message
  2.  a callback query
- If `Service.next` returns `last = True`, active `Service` instance is destroyed
- If no active `Service` instance is found for the user, the `help` service is triggered.

## Services (Examples)

Refer to the following example,

`MakeBooking.setup`:

- sets up an empty Booking instance
- creates a calendar object
- waits for callback `set_date_cb` (if another message is received, `setup` is repeated since `next_step = None`)

`MakeBooking.set_n_pax`:

- sets the number of pax and ask the question of "What is the purpose?"
- waits for next message to trigger `set_purpose`

```python
class MakeBooking(Service):
    commands = ["book"]
    data: Booking = None

    def setup(self, args: HandlerArgs) -> HandlerResult:

        self.data = Booking(user=args.user)

        calendar, step = cal(min_date=date.today()).build()

        args.bot.send_message(
            args.message.chat.id, f"Select {LSTEP[step]}", reply_markup=calendar
        )

        return HandlerResult(next_step=None, success=True, last=False)

    def set_date_cb(self, bot: TeleBot, message: Message, date: date) -> None:
        print("Date is set")
        self.data.date = date
        bot.send_message(message.chat.id, "What is the number of pax?")
        self.set_next_step("set_n_pax")

    def set_n_pax(self, args: HandlerArgs) -> HandlerResult:

        self.data.n_pax = int(args.message.text)
        args.bot.send_message(args.message.chat.id, "What is the purpose?")

        return HandlerResult(next_step="set_purpose", success=True, last=False)

    def set_purpose(self, args: HandlerArgs) -> HandlerResult:

        self.data.purpose = args.message.text
        args.bot.send_message(
            args.message.chat.id,
            "\n".join(
                [
                    "Booking is made!",
                    f"*Date*: {str(self.data.date)}",
                    f"No. Pax: {str(self.data.n_pax)}",
                    f"Purpose: {str(self.data.purpose)}",
                ]
            ),
        )

        return HandlerResult(next_step=None, success=True, last=True)


@bot.callback_query_handler(func=cal.func())
def cal_callback(cb_query: CallbackQuery):
    result, key, step = cal().process(cb_query.data)
    id_ = cb_query.from_user.id

    if not result and key:
        bot.edit_message_text(
            f"Select {LSTEP[step]}",
            cb_query.message.chat.id,
            cb_query.message.message_id,
            reply_markup=key,
        )
    elif result:
        service: MakeBooking = Context.get_service(id_, "book")

        if service is not None:
            service.set_date_cb(bot, cb_query.message, result)

        bot.edit_message_text(
            f"You selected {result}",
            cb_query.message.chat.id,
            cb_query.message.message_id,
        )
```
