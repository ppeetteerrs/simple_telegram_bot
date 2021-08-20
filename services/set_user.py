from utils.classes import HandlerArgs, HandlerResult, Service, User


class SetUser(Service):
    commands = ["start"]
    data: User = None

    def setup(self, args: HandlerArgs) -> HandlerResult:

        args.bot.send_message(
            args.message.chat.id,
            "\n".join(
                [
                    f"Greetings, {args.message.from_user.full_name}, welcome on board!",
                    "What is your email address?",
                ]
            ),
        )

        return HandlerResult(next_step="set_email", success=True, last=False)

    def set_email(self, args: HandlerArgs) -> HandlerResult:

        self.data = User(
            id_=args.message.from_user.id,
            username=args.message.from_user.username,
            email=args.message.text,
        )
        self.data.save()
        args.bot.send_message(
            args.message.chat.id,
            "\n".join(
                [
                    f"Your email is registered!",
                    "How may I help you? (type /help for more info)",
                ]
            ),
        )

        return HandlerResult(next_step=None, success=True, last=True)
