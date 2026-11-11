from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from desktop.__main__ import main

    raise SystemExit(main())
