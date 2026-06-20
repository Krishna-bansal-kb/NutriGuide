from sklearn.tree import DecisionTreeClassifier
import io
import pandas as pd
import webbrowser
import plotly.express as px
import os

from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas

app = Flask(__name__)

food_db = pd.read_csv("food_database.csv")
ml_data = pd.read_csv(
    "food_health_dataset.csv"
)

X = ml_data[
[
    "Calories",
    "Protein",
    "Fat",
    "Sugar",
    "Sodium"
]
]

y = ml_data["Label"]

model = DecisionTreeClassifier()

model.fit(X, y)

latest_report={}
@app.route('/')

def home():
    foods = food_db['Food'].tolist()

    return render_template('index.html', foods=foods)


@app.route('/analyze', methods=['POST'])
def analyze():

    
    # User Details
    name = request.form['name']
    age = int(request.form['age'])
    height = float(request.form['height'])
    weight = float(request.form['weight'])

    # Food Details
    food = request.form['food']
    condition = request.form['condition']
    goal = request.form['goal']

    disease_diet = []
    foods_to_avoid = []

    # BMI Calculation
    height_m = height / 100
    bmi = weight / (height_m * height_m)

    if bmi < 18.5:
        bmi_status = "Underweight"
    elif bmi < 25:
        bmi_status = "Normal"
    elif bmi < 30:
        bmi_status = "Overweight"
    else:
        bmi_status = "Obese"

    # Personalized Insight

if bmi < 18.5:
    personalized_insight = (
        f"{name}, your BMI indicates that you are underweight. "
        "A gradual increase in calorie and protein intake may help improve your health."
    )

elif bmi < 25:
    personalized_insight = (
        f"{name}, your BMI is within the healthy range. "
        "Maintaining balanced nutrition and regular physical activity is recommended."
    )

elif bmi < 30:
    personalized_insight = (
        f"{name}, your BMI indicates overweight status. "
        "Reducing excess calories and increasing physical activity may help."
    )

else:
    personalized_insight = (
        f"{name}, your BMI indicates obesity. "
        "A structured diet plan and regular exercise are strongly recommended."
    )

    # Daily Calorie Requirement
    daily_calories = round(weight * 30)
    water_intake = round((weight*35)/1000,2)

    # Search Food Database
    food_list = [f.strip() for f in food.split(",")]

    results = food_db[
        food_db['Food'].str.lower().isin(
            [x.lower() for x in food_list]
        )
    ]

    if results.empty:
        return "Food not found in database."

    food_info = results.iloc[0]
    food_records = results.to_dict('records')
    prediction = model.predict(
[[
    food_info["Calories"],
    food_info["Protein"],
    food_info["Fat"],
    food_info["Sugar"],
    food_info["Sodium"]
]]
)[0]

    total_calories = results['Calories'].sum()
    total_protein = results['Protein'].sum()
    total_fat = results['Fat'].sum()
    total_carbs = results['Carbs'].sum()
    total_sugar = results['Sugar'].sum()

# =========================
    # Interactive Plotly Graph
    # =========================

    graph_df = pd.DataFrame({
        "Nutrient": [
            "Protein",
            "Fat",
            "Carbs",
            "Sugar"
        ],
        "Amount": [
            total_protein,
            total_fat,
            total_carbs,
            total_sugar
        ]
    })

    fig = px.pie(
        graph_df,
        values="Amount",
        names="Nutrient",
        title="Meal Nutrient Composition"
    )

    fig.update_layout(
        template="plotly_white"
    )

    graph_html = fig.to_html(
        full_html=False
    )

    # =========================
    # Health Score Calculation
    # =========================

    score = 100

    sugar = float(food_info['Sugar'])
    sodium = float(food_info['Sodium'])
    cholesterol = float(food_info['Cholesterol'])
    protein = float(food_info['Protein'])
    fat = float(food_info['Fat'])
    carbs = float(food_info['Carbs'])

    diet_plan = []

    if goal == "Weight Loss":
        diet_plan = [
            "Breakfast: Oats + Apple",
            "Lunch: Dal + Roti + Salad",
            "Dinner: Soup + Paneer"
        ]

    elif goal == "Muscle Gain":
        diet_plan = [
    f"Breakfast: Eggs and milk",
    f"Lunch: Rice, chicken/paneer and vegetables",
    f"Dinner: Paneer and chapati",
    f"Target Protein: {round(weight*1.6)} g/day"
]

    elif goal == "Weight Gain":
        diet_plan = [
    f"Breakfast: Banana shake with nuts",
    f"Lunch: Rice, dal and paneer",
    f"Dinner: Chapati and vegetables",
    f"Target Calories: {daily_calories+400} kcal/day"
]

# Negative factors

# Sugar
    if sugar > 20:
        score -= 20
    elif sugar > 10:
        score -= 10

# Sodium
    if sodium > 500:
        score -= 20
    elif sodium > 200:
        score -= 10

# Cholesterol
    if cholesterol > 100:
        score -= 15
    elif cholesterol > 50:
        score -= 8

# Fat
    if fat > 20:
        score -= 15
    elif fat > 10:
        score -= 8

# Carbohydrates
    if carbs > 60:
        score -= 10
    elif carbs > 40:
        score -= 5

# Positive factors

# Protein
    if protein > 20:
        score += 15
    elif protein > 10:
        score += 10
    elif protein > 5:
        score += 5

    # Final limit
    score = max(0, min(score, 100))

    if score >= 85:
        health_rating = "Excellent"
    elif score >= 70:
        health_rating = "Good"
    elif score >= 50:
        health_rating = "Moderate"
    else:
        health_rating = "Poor"

    recommendations = []
# Smart Nutrient Analysis

if total_sugar > 50:
    recommendations.append(
        "Your meal contains a high amount of sugar. Consider reducing sugary foods."
    )

if total_fat > 70:
    recommendations.append(
        "Fat content is relatively high. Prefer healthier fat sources."
    )

if total_protein < 20:
    recommendations.append(
        "Protein intake appears low. Consider adding pulses, milk, eggs or paneer."
    )

if total_calories > daily_calories:
    recommendations.append(
        "This meal exceeds your estimated daily calorie requirement."
    )

if total_carbs > 250:
    recommendations.append(
        "Carbohydrate intake is relatively high. Balance it with protein and fibre."
    )
    
    
    # Disease Analysis

    if condition == "Diabetes":
        if food_info['GI'] > 55:
            recommendations.append(
    f"The selected meal has a GI value of {food_info['GI']}, which may cause faster blood sugar spikes."
)
        else:
            recommendations.append(
    f"The GI value of {food_info['GI']} is relatively diabetes-friendly."
)

    elif condition == "Hypertension":
        if food_info['Sodium'] > 200:
            recommendations.append(
                "⚠ High sodium content."
            )
        else:
            recommendations.append(
                "✅ Low sodium food."
            )

    elif condition == "High Cholesterol":
        if food_info['Cholesterol'] > 50:
            recommendations.append(
                "⚠ High cholesterol content."
            )
        else:
            recommendations.append(
                "✅ Suitable for cholesterol management."
            )

    # Goal Recommendations

    if goal == "Weight Loss":
        recommendations.append(
            "Focus on calorie deficit and high-fiber foods."
        )

    elif goal == "Muscle Gain":
        recommendations.append(
            "Increase protein intake and strength training."
        )

    elif goal == "Weight Gain":
        recommendations.append(
            "Increase healthy calorie intake."
        )

    # Disease Specific Diet Plans

    if condition == "Diabetes":

        disease_diet = [
            "Breakfast: Oats + Boiled Egg",
            "Lunch: Brown Rice + Dal",
            "Dinner: Salad + Paneer"
        ]

        foods_to_avoid = [
            "Sugar",
            "Soft Drinks",
            "White Bread",
            "Sweets"
        ]

    elif condition == "Hypertension":

        disease_diet = [
            "Breakfast: Banana + Oats",
            "Lunch: Brown Rice + Vegetables",
            "Dinner: Soup + Salad"
        ]

        foods_to_avoid = [
            "Pickles",
            "Chips",
            "Processed Foods"
        ]

    elif condition == "High Cholesterol":

        disease_diet = [
            "Breakfast: Oats + Fruits",
            "Lunch: Dal + Chapati",
            "Dinner: Vegetables + Soup"
        ]

        foods_to_avoid = [
            "Butter",
            "Fast Food",
            "Fried Foods"
        ]

    # Exercise Recommendations

    exercise = []

    if goal == "Weight Loss":
        exercise = [
    "45 min brisk walking",
    "20 min jogging",
    "Cycling 30 min",
    f"Estimated calorie burn target: {round(weight*5)} kcal/day"
]
    elif goal == "Muscle Gain":
        exercise = [
    "Strength Training",
    "Push-ups",
    "Squats",
    f"Protein goal: {round(weight*1.6)} g/day"
]

    elif goal == "Weight Gain":
        exercise = [
    "Weight Training",
    "Compound Exercises",
    "Light Cardio",
    f"Daily calorie surplus target: 300-500 kcal"
]
    global latest_report

    history_file = "history.csv"

    try:
        history_df = pd.read_csv(history_file)
    except:
        history_df = pd.DataFrame(
            columns=["Name", "Food", "BMI", "Score"]
        )

    history_df.loc[len(history_df)] = [
        name,
        food,
        round(bmi, 2),
        score
    ]

    history_df.to_csv(
        history_file,
        index=False
    )

    latest_report = {
        "name": name,
        "age": age,
        "bmi": round(bmi, 2),
        "bmi_status": bmi_status,
        "daily_calories": daily_calories,
        "food": food_info['Food'],
        "calories": food_info['Calories'],
        "protein": food_info['Protein'],
        "fat": food_info['Fat'],
        "carbs": food_info['Carbs'],
        "sugar": food_info['Sugar'],
        "health_score": score,
        "food_quality": health_rating,
        "recommendations": recommendations,
        "exercise": exercise
    }


    return render_template (
        'result.html',
        food_info=food_info,
        recommendations=recommendations,
        bmi=round(bmi, 2),
        bmi_status=bmi_status,
        name=name,
        age=age,
        daily_calories=daily_calories,
        exercise=exercise,
        score = score,
        health_rating= health_rating,
        diet_plan= diet_plan,
        water_intake=water_intake,
        disease_diet=disease_diet,
        foods_to_avoid=foods_to_avoid,
        total_calories=total_calories,
        total_protein=total_protein,
        total_fat=total_fat,
        total_carbs=total_carbs,
        total_sugar=total_sugar,
        prediction= prediction,
        food_records=food_records,
        graph_html=graph_html,
        personalized_insight=personalized_insight,
    )

@app.route('/download_pdf')
def download_pdf():

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer)

    # Starting Position
    y = 800

    # ======================
    # HEADER
    # ======================

    p.setFont("Helvetica-Bold", 24)
    p.drawString(150, y, "NUTRIGUIDE")

    y -= 25

    p.setFont("Helvetica", 12)
    p.drawString(
        90,
        y,
        "Personalized Nutrition & Health Assessment Report"
    )

    y -= 20

    p.line(50, y, 550, y)

    y -= 35

    # ======================
    # USER INFORMATION
    # ======================

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "USER INFORMATION")

    y -= 25

    p.setFont("Helvetica", 12)

    p.drawString(
        70,
        y,
        f"Name: {latest_report['name']}"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Age: {latest_report['age']}"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"BMI: {latest_report['bmi']}"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Health Status: {latest_report['bmi_status']}"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Daily Calorie Requirement: {latest_report['daily_calories']} kcal/day"
    )

    y -= 35

    # ======================
    # FOOD INFORMATION
    # ======================

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "FOOD INFORMATION")

    y -= 25

    p.setFont("Helvetica", 12)

    p.drawString(
        70,
        y,
        f"Food: {latest_report['food']}"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Calories: {latest_report['calories']} kcal"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Protein: {latest_report['protein']} g"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Fat: {latest_report['fat']} g"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Carbohydrates: {latest_report['carbs']} g"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Sugar: {latest_report['sugar']} g"
    )

    y -= 35

    # ======================
    # HEALTH SCORE
    # ======================

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "HEALTH ASSESSMENT")

    y -= 25

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        70,
        y,
        f"Health Score: {latest_report['health_score']}/100"
    )

    y -= 20

    p.drawString(
        70,
        y,
        f"Food Quality: {latest_report['food_quality']}"
    )

    y -= 35

    # ======================
    # RECOMMENDATIONS
    # ======================

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "HEALTH RECOMMENDATIONS")

    y -= 25

    p.setFont("Helvetica", 12)

    for rec in latest_report['recommendations']:
        p.drawString(
            70,
            y,
            f"- {rec}"
        )
        y -= 20

    y -= 15

    # ======================
    # EXERCISES
    # ======================

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "RECOMMENDED EXERCISES")

    y -= 25

    p.setFont("Helvetica", 12)

    for ex in latest_report['exercise']:
        p.drawString(
            70,
            y,
            f"- {ex}"
        )
        y -= 20

    # ======================
    # FOOTER
    # ======================

    p.line(50, 50, 550, 50)

    p.setFont("Helvetica-Oblique", 10)

    p.drawString(
        50,
        30,
        "Generated by NutriGuide | Final Year Project"
    )

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="NutriGuide_Report.pdf",
        mimetype="application/pdf"
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/history')
def history():

    try:
        history_df = pd.read_csv("history.csv")

        return history_df.to_html(
            classes='table',
            index=False
        )

    except:
        return "No history available."

if __name__ == "__main__":
       app.run(host="0.0.0.0", port=5000)
