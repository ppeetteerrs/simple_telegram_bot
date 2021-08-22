class BotState:
    """
    Bot context
        service_classes: mapping from command to service
        user_data: mapping from user ID to active service

        add_service: register a new service
        handle: handle a message
        get_service: helper function to get active service of a user
    """

    service_classes: Dict[str, Type[Service]] = {}
    user_data: Dict[str, Service] = {}

    @classmethod
    def add_service(cls, service_class: Type[Service]) -> None:
        for command in service_class.commands:
            cls.service_classes[command] = service_class

    @classmethod
    def handle(cls, args: HandlerArgs) -> bool:

        # Get currently active service for user
        id_ = args.message.from_user.id
        current_service = cls.user_data.get(id_)
        command = (
            args.command if args.command in cls.service_classes else "help"
        )

        # Start new service if no command / no active service
        if current_service is None or args.command is not None:
            current_service = cls.user_data[id_] = cls.service_classes[
                command
            ]()

        # Run 1 step in the service and wait for next message
        result = current_service.next(args)

        # Clear active service on successful last operation
        if result.success and result.last:
            cls.user_data.pop(id_)

        return result.success

    @classmethod
    def get_service(cls, id_: int, command: str) -> Optional[Service]:
        service = cls.user_data.get(id_)
        if service is None or command not in service.commands:
            return None
        else:
            return service
