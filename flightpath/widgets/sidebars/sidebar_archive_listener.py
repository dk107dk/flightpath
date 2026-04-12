from csvpath.managers.metadata import Metadata


class SidebarArchiveListener:
    def __init__(self, *, item):
        self.item = item
        print(f"adding SALx for {id(item)}")

    def metadata_update(self, mdata: Metadata) -> None:
        self.mdata = mdata
        self.item.metadata["run_dir"] = mdata.run_home
        self.item.subtitle.setText(mdata.run_home)
        self.mdata = None
