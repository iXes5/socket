# Upload button
    upload_image = PhotoImage(file="image/upload.png")
    upload_button = tk.Button(secondary_window, image=upload_image, bd=0, command=select_file_to_upload)
    upload_button.grid(row=0, column=0, padx=10)
    upload_button.image = upload_image

    # Download button
    download_image = PhotoImage(file="image/download.png")
    download_button = tk.Button(secondary_window, image=download_image, bg="linen", bd=0, command=lambda: select_file_to_download(root))
    download_button.grid(row=0, column=1, padx=10)
    download_button.image = download_image

    # Disconnect button
    disconnect_image = PhotoImage(file="image/disconnect.png")
    disconnect_button = tk.Button(secondary_window, image=disconnect_image, bg="linen", bd=0, command=lambda: disconnect_to_server(secondary_window))
    disconnect_button.grid(row=0, column=2, padx=10)
    disconnect_button.image = disconnect_image

    secondary_window.mainloop()
