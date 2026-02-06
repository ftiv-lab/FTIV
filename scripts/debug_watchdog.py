import logging

from PySide6.QtCore import QTimer

logger = logging.getLogger("connector_watchdog")


class ConnectorWatchdog:
    def __init__(self, main_window):
        self.main_window = main_window
        self.timer = QTimer(main_window)
        self.timer.timeout.connect(self.check_connectors)
        self.timer.start(5000)  # Check every 5 seconds
        logger.info("ConnectorWatchdog started.")

    def check_connectors(self):
        try:
            wm = self.main_window.window_manager
            connectors = wm.connectors
            logger.info(f"--- Watchdog: {len(connectors)} Connectors ---")

            for i, conn in enumerate(connectors):
                try:
                    import shiboken6

                    valid = shiboken6.isValid(conn)

                    if not valid:
                        logger.error(f"Connector #{i} is INVALID (Deleted C++ object)")
                        continue

                    visible = conn.isVisible()
                    hidden_flag = conn.isHidden()
                    # geo = conn.geometry()  <-- Unused, removed to fix lint

                    sw = getattr(conn, "start_window", None)
                    ew = getattr(conn, "end_window", None)
                    sw_valid = shiboken6.isValid(sw) if sw else False
                    ew_valid = shiboken6.isValid(ew) if ew else False

                    status = "OK" if visible and sw_valid and ew_valid else "INFO"
                    if hidden_flag:
                        status = "HIDDEN"

                    msg = (
                        f"#{i}: Status={status}, Vis={visible}, HiddenFlag={hidden_flag}, "
                        f"Start={sw_valid}, End={ew_valid}"
                    )

                    if status == "PROBLEM":
                        logger.warning(msg)
                    else:
                        logger.debug(msg)

                except Exception as e:
                    logger.error(f"Error checking connector #{i}: {e}")

        except Exception as e:
            logger.error(f"Watchdog global error: {e}")


def install(main_window):
    main_window._watchdog = ConnectorWatchdog(main_window)
