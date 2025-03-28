from minecraft_log_checker import visualize_player_sessions

if __name__ == "__main__":
    # Use default config values
    visualize_player_sessions()

    # Or specify custom dates and output path:
    # visualize_player_sessions(
    #     start_date="2024-03-01",
    #     end_date="2024-03-25",
    #     output_path="output/my_minecraft_sessions.png"
    # )
