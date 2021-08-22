import re
from typing import Optional

from utils.classes import HandlerArgs, HandlerResult, Service, User


class ResetEmail(Service):
    commands = ["start", "reset_email"]
    data: Optional[User] = None

    def setup(self, args: HandlerArgs) -> HandlerResult:
        """Sends greetings message"""

        args.bot.send_message(
            args.message.chat.id,
            "\n".join(
                [
                    f"Greetings, {args.message.from_user.full_name}, welcome on board!",
                    "What is your NTU email address?",
                ]
            ),
        )

        # Wait for email address input
        return HandlerResult(next_step="set_email", success=True, last=False)

    def set_email(self, args: HandlerArgs) -> HandlerResult:
        """Create new user data using email."""

        email = (
            args.message.text.lower().strip()
            if args.message.text is not None
            else ""
        )
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        if re.fullmatch(regex, email) and "ntu.edu.sg" in email:

            # If email is valid, create and save user info
            self.data = User(
                id_=args.message.from_user.id,
                username=args.message.from_user.username,
                email=email,
            )
            self.data.save()

            args.bot.send_message(
                args.message.chat.id,
                "\n".join(
                    [
                        f"Your email {email} is registered!",
                        "How may I help you? (type /help for more info)",
                    ]
                ),
            )

            # End of ResetEmail Service
            return HandlerResult(next_step=None, success=True, last=True)

        else:

            # Ask for a valid email
            args.bot.send_message(
                args.message.chat.id,
                "\n".join(
                    [
                        f"Your email {email} is invalid :(",
                        "Please enter a valid NTU email address.",
                    ]
                ),
            )

            # Repeat the step
            return HandlerResult(
                next_step="set_email", success=False, last=False
            )
