import argparse
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Set seed for reproducibility
np.random.seed(42)

# Define crop profiles based on actual agronomic science.
# Structure: { crop_name: { N_range, P_range, K_range, temp_range, humidity_range, pH_range, rainfall_range } }
crop_profiles = {
    'Rice': {
        'N': (60, 100), 'P': (35, 60), 'K': (35, 50),
        'temp': (20, 36), 'humidity': (80, 99), 'pH': (5.0, 6.8), 'rainfall': (150, 300)
    },
    'Maize': {
        'N': (60, 90), 'P': (40, 70), 'K': (25, 50),
        'temp': (18, 35), 'humidity': (55, 80), 'pH': (5.5, 7.3), 'rainfall': (60, 160)
    },
    'Chickpea': {
        'N': (15, 35), 'P': (40, 65), 'K': (15, 35),
        'temp': (15, 27), 'humidity': (15, 40), 'pH': (6.0, 8.0), 'rainfall': (25, 60)
    },
    'Cotton': {
        'N': (70, 110), 'P': (35, 60), 'K': (35, 65),
        'temp': (22, 38), 'humidity': (40, 75), 'pH': (5.8, 8.0), 'rainfall': (60, 110)
    },
    'Coconut': {
        'N': (60, 90), 'P': (15, 35), 'K': (130, 190),
        'temp': (24, 38), 'humidity': (75, 95), 'pH': (5.2, 7.8), 'rainfall': (120, 260)
    },
    'Coffee': {
        'N': (80, 110), 'P': (30, 50), 'K': (70, 100),
        'temp': (15, 28), 'humidity': (60, 90), 'pH': (5.0, 6.2), 'rainfall': (130, 240)
    },
    'Banana': {
        'N': (80, 120), 'P': (60, 90), 'K': (120, 200),
        'temp': (20, 35), 'humidity': (70, 92), 'pH': (5.5, 7.5), 'rainfall': (100, 250)
    },
    'Mango': {
        'N': (30, 60), 'P': (20, 45), 'K': (30, 60),
        'temp': (24, 40), 'humidity': (45, 75), 'pH': (5.5, 7.0), 'rainfall': (40, 100)
    },
    'Grapes': {
        'N': (20, 50), 'P': (20, 40), 'K': (65, 100),
        'temp': (15, 33), 'humidity': (40, 70), 'pH': (5.5, 7.0), 'rainfall': (20, 60)
    },
    'Watermelon': {
        'N': (80, 110), 'P': (40, 65), 'K': (40, 65),
        'temp': (22, 38), 'humidity': (45, 80), 'pH': (5.5, 6.8), 'rainfall': (40, 95)
    },
    'Orange': {
        'N': (60, 90), 'P': (10, 30), 'K': (40, 80),
        'temp': (16, 35), 'humidity': (60, 85), 'pH': (5.5, 7.5), 'rainfall': (60, 130)
    },
    'Papaya': {
        'N': (50, 85), 'P': (45, 70), 'K': (60, 105),
        'temp': (20, 36), 'humidity': (60, 85), 'pH': (5.5, 7.2), 'rainfall': (60, 160)
    }
}


def synthesize_dataset(samples_per_crop):
    rows = []
    for crop, profile in crop_profiles.items():
        for _ in range(samples_per_crop):
            n = max(0, int(np.random.uniform(*profile['N']) + np.random.normal(0, 3)))
            p = max(0, int(np.random.uniform(*profile['P']) + np.random.normal(0, 3)))
            k = max(0, int(np.random.uniform(*profile['K']) + np.random.normal(0, 4)))
            temp = round(float(np.random.uniform(*profile['temp']) + np.random.normal(0, 0.5)), 2)
            humidity = min(100.0, max(0.0, round(float(np.random.uniform(*profile['humidity']) + np.random.normal(0, 1)), 2)))
            ph = min(14.0, max(0.0, round(float(np.random.uniform(*profile['pH']) + np.random.normal(0, 0.1)), 2)))
            rainfall = max(0.0, round(float(np.random.uniform(*profile['rainfall']) + np.random.normal(0, 5)), 2))
            rows.append({
                'N': n,
                'P': p,
                'K': k,
                'temperature': temp,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall,
                'label': crop
            })
    return pd.DataFrame(rows)


def train_and_save(dataset, model_path, labels_path):
    X = dataset.drop(columns=['label'])
    y = dataset['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"Generated dataset shape: {dataset.shape}")
    print(f"Training set shape: {X_train.shape}, Testing set shape: {X_test.shape}")

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy on Test Set: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Saved model '{model_path}' successfully.")

    crops_list = sorted(dataset['label'].unique())
    with open(labels_path, 'wb') as f:
        pickle.dump(crops_list, f)
    print(f"Saved label classes: {crops_list}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train the AgroSmart AI crop recommendation model.')
    parser.add_argument('--samples-per-crop', type=int, default=150, help='Number of synthetic rows generated per crop.')
    parser.add_argument('--output-model', type=str, default='crop_recommender.pkl', help='Output file path for the trained model.')
    parser.add_argument('--output-labels', type=str, default='label_classes.pkl', help='Output file path for the label classes pickle.')
    parser.add_argument('--export-dataset', type=str, default=None, help='Optional CSV path to export the generated training dataset.')
    args = parser.parse_args()

    dataset = synthesize_dataset(args.samples_per_crop)
    if args.export_dataset:
        dataset.to_csv(args.export_dataset, index=False)
        print(f"Exported dataset to {args.export_dataset}")

    train_and_save(dataset, args.output_model, args.output_labels)
