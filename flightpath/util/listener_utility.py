class ListenerUtility:
    @classmethod
    def assure_activation(cls, main) -> None:
        if main is None:
            raise ValueError("Main cannot be None")
        _ = main.csvpath_config.get(section="listeners", name="activation.file")
        if _ is None:
            main.csvpath_config.set(
                section="listeners",
                name="activation.file",
                value="from csvpath.managers.files.files_activation_listener import FileActivationListener",
            )
            main.csvpath_config.save_config()
            cls.add_to_groups_if(main=main, name="activation")

    @classmethod
    def assure_webhooks(cls, main) -> None:
        if main is None:
            raise ValueError("Main cannot be None")
        _ = main.csvpath_config.get(section="listeners", name="webhook.results")
        if _ is None:
            main.csvpath_config.set(
                section="listeners",
                name="webhook.results",
                value="from csvpath.managers.integrations.webhook.webhook_results_listener import WebhookResultsListener",
            )
            main.csvpath_config.save_config()
            cls.add_to_groups_if(main=main, name="webhook")

    @classmethod
    def add_to_groups_if(self, *, main, name: str) -> None:
        if main is None:
            raise ValueError("Main cannot be None")
        if name is None:
            raise ValueError("Group name cannot be None")
        name = name.strip()
        t = main.csvpath_config.get(section="listeners", name="groups")
        if t is None:
            t = name
        t = t.strip()
        ts = [t.strip() for t in t.split(",")]

        if name in ts:
            return
        ts.append(name)
        nt = ",".join(ts)

        main.csvpath_config.get(section="listeners", name="groups", value=nt)
        main.csvpath_config.save_config()
