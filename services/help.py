from utils.classes import HandlerArgs, HandlerResult, Service


class Help(Service):
    commands = ["help"]
    data = None

    def setup(self, args: HandlerArgs) -> HandlerResult:

        args.bot.send_message(
            args.message.chat.id,
            "It's just a joke, there is no help available :) Maybe try typing /book?",
        )

        return HandlerResult(next_step=None, success=True, last=True)
