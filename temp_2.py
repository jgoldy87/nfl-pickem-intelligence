
import nflreadpy as nfl
import numpy as np
import pandas as pd

SEASONS = list(range(2021, 2026))
FIRST_TEST_WEEK = 5
RIDGE_VALUES = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]

# Separate regularization for the home-field parameter.
HOME_RIDGE = 10.0

schedule = nfl.load_schedules(
    seasons=SEASONS
).to_pandas()

games = schedule[
    (schedule["game_type"] == "REG")
    & schedule["home_score"].notna()
    & schedule["away_score"].notna()
].copy()

games["margin"] = (
    games["home_score"] - games["away_score"]
).astype(float)

teams = sorted(
    set(games["home_team"]) | set(games["away_team"])
)

team_to_idx = {
    team: idx for idx, team in enumerate(teams)
}

n_teams = len(teams)


def build_matrix(data, include_home):
    """Create a team-difference design matrix."""
    extra = 1 if include_home else 0
    X = np.zeros((len(data), n_teams + extra))

    for row_idx, (_, game) in enumerate(data.iterrows()):
        X[row_idx, team_to_idx[game["home_team"]]] = 1.0
        X[row_idx, team_to_idx[game["away_team"]]] = -1.0

        if include_home:
            X[row_idx, -1] = 1.0

    return X


def fit_model(train, ridge, include_home):
    X = build_matrix(train, include_home)
    y = train["margin"].to_numpy()

    penalty = np.full(X.shape[1], ridge)

    if include_home:
        penalty[-1] = HOME_RIDGE

    coefficients = np.linalg.solve(
        X.T @ X + np.diag(penalty),
        X.T @ y,
    )

    return coefficients


def predict_games(test, coefficients, include_home):
    X = build_matrix(test, include_home)
    return X @ coefficients


predictions = []

for season in SEASONS:
    season_games = games[
        games["season"] == season
    ].copy()

    for week in sorted(season_games["week"].unique()):
        if week < FIRST_TEST_WEEK:
            continue

        train = season_games[
            season_games["week"] < week
        ]

        test = season_games[
            season_games["week"] == week
        ]

        if train.empty or test.empty:
            continue

        for ridge in RIDGE_VALUES:
            for include_home in [False, True]:
                coefficients = fit_model(
                    train,
                    ridge,
                    include_home,
                )

                predicted = predict_games(
                    test,
                    coefficients,
                    include_home,
                )

                home_advantage = (
                    coefficients[-1] if include_home else 0.0
                )

                for (_, game), pred in zip(
                    test.iterrows(), predicted
                ):
                    actual = game["margin"]

                    predictions.append({
                        "season": season,
                        "week": week,
                        "ridge": ridge,
                        "home_field": include_home,
                        "actual_margin": actual,
                        "predicted_margin": pred,
                        "absolute_error": abs(actual - pred),
                        "squared_error": (actual - pred) ** 2,
                        "winner_correct": (
                            np.sign(actual) == np.sign(pred)
                        ) if actual != 0 else np.nan,
                        "home_advantage": home_advantage,
                    })


results = pd.DataFrame(predictions)

summary = (
    results.groupby(
        ["ridge", "home_field"],
        as_index=False,
    )
    .agg(
        games=("absolute_error", "size"),
        mae=("absolute_error", "mean"),
        mse=("squared_error", "mean"),
        winner_accuracy=("winner_correct", "mean"),
        avg_home_advantage=("home_advantage", "mean"),
    )
)

summary["rmse"] = np.sqrt(summary["mse"])

summary["winner_accuracy"] *= 100

summary = summary.sort_values(
    ["mae", "rmse"],
    ascending=True,
)

display_columns = [
    "ridge",
    "home_field",
    "games",
    "mae",
    "rmse",
    "winner_accuracy",
    "avg_home_advantage",
]

display = summary[display_columns].copy()

for col in [
    "mae",
    "rmse",
    "winner_accuracy",
    "avg_home_advantage",
]:
    display[col] = display[col].round(2)

print("\nNFL HISTORICAL RATING BACKTEST")
print(f"Seasons: {SEASONS[0]}-{SEASONS[-1]}")
print(f"Predictions begin: Week {FIRST_TEST_WEEK}")
print("=" * 100)
print(display.to_string(index=False))

best = summary.iloc[0]

print("\nBEST MODEL BY MAE")
print("=" * 60)
print(f"Ridge penalty: {best['ridge']}")
print(f"Include home field: {best['home_field']}")
print(f"Games tested: {int(best['games'])}")
print(f"MAE: {best['mae']:.2f} points")
print(f"RMSE: {best['rmse']:.2f} points")
print(f"Winner accuracy: {best['winner_accuracy']:.1f}%")
print(
    "Average fitted home advantage: "
    f"{best['avg_home_advantage']:.2f} points"
)
