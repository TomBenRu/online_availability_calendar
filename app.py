from collections import defaultdict

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta, date
import random
import json

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Dummy Planungs-Perioden (müssen nach 'start' sortiert sein)
plan_periods = [
    {'start': date(2024, 11, 1), 'end': date(2024, 11, 11), 'deadline': date(2024, 11, 10), 'message': 'Planungsperiode 1\nErledige deine Einträge bitte bis zur Deadline.'}, 
    {'start': date(2024, 11, 12), 'end': date(2024, 11, 24), 'deadline': date(2024, 11, 23), 'message': 'Planungsperiode 2'}, 
    {'start': date(2024, 11, 25), 'end': date(2024, 12, 10), 'deadline': date(2024, 12, 9), 'message': 'Planungsperiode 3'}, 
    {'start': date(2024, 12, 11), 'end': date(2025, 1, 10), 'deadline': date(2025, 1, 9), 'message': 'Planungsperiode 4'}, 
    {'start': date(2025, 1, 11), 'end': date(2025, 1, 20), 'deadline': date(2025, 1, 19), 'message': 'Planungsperiode 5'}, 
    {'start': date(2025, 1, 21), 'end': date(2025, 2, 10), 'deadline': date(2025, 2, 9), 'message': 'Planungsperiode 6'}, 
    {'start': date(2025, 2, 11), 'end': date(2025, 2, 20), 'deadline': date(2025, 2, 19), 'message': 'Planungsperiode 7'}, 
    {'start': date(2025, 2, 21), 'end': date(2025, 3, 10), 'deadline': date(2025, 3, 9), 'message': 'Planungsperiode 8'}, 
    {'start': date(2025, 3, 11), 'end': date(2025, 3, 20), 'deadline': date(2025, 3, 19), 'message': 'Planungsperiode 9'}, 
    {'start': date(2025, 3, 21), 'end': date(2025, 4, 10), 'deadline': date(2025, 4, 9), 'message': 'Planungsperiode 10'}, 
    {'start': date(2025, 4, 11), 'end': date(2025, 4, 20), 'deadline': date(2025, 4, 19), 'message': 'Planungsperiode 11'}, 
    {'start': date(2025, 4, 21), 'end': date(2025, 5, 10), 'deadline': date(2025, 5, 9), 'message': 'Planungsperiode 12'},
    {'start': date(2025, 5, 10), 'end': date(2025, 5, 31), 'deadline': date(2025, 5, 9), 'message': 'Planungsperiode 13'},
    {'start': date(2025, 6, 1), 'end': date(2025, 6, 30), 'deadline': date(2025, 5, 9), 'message': 'Planungsperiode 14'},
    {'start': date(2025, 7, 1), 'end': date(2025, 7, 31), 'deadline': date(2025, 6, 9), 'message': 'Planungsperiode 15'},]

# Globale Konstanten
# Monatsnamen für die Anzeige
month_names = {
    1: 'Januar',
    2: 'Februar',
    3: 'März',
    4: 'April',
    5: 'Mai',
    6: 'Juni',
    7: 'Juli',
    8: 'August',
    9: 'September',
    10: 'Oktober',
    11: 'November',
    12: 'Dezember'
}
# Farben für Planungsperioden
colors_for_periods = ['bg-blue-800/40', 'bg-emerald-800/40', 'bg-violet-800/40']
# Farben für die Icons
colors_times_of_day = {
    'morning': {
        'unchecked': 'gray-400',
        'checked': 'yellow-400'
    },
    'afternoon': {
        'unchecked': 'gray-400',
        'checked': 'orange-400'
    },
    'evening': {
        'unchecked': 'gray-400',
        'checked': 'red-500'
    }
}
# Farben für die Notifikation:
notification_colors = {
    'background': {
        'checked': 'green-100', 
        'unchecked': 'red-100'
        },  
    'border': {
        'checked': 'green-400', 
        'unchecked': 'red-400'
        }, 
    'text': {
        'checked': 'green-700',
        'unchecked': 'red-700'
        }
}
# Übersetze die Periode ins Deutsche
period_translation = {
    "morning": "Morgen",
    "afternoon": "Nachmitt.",
    "evening": "Abend"
}

# Globale Variablen
selected_times: defaultdict[str, set] = defaultdict(set)  # Dictionary für ausgewählte Zeiten (später durch DB ersetzen)
user_notes = {}  # Dictionary für Anmerkungen (später durch DB ersetzen)

@app.get("/", name="index", response_class=HTMLResponse)
async def index(request: Request):
    """Zeigt die Hauptseite mit Login-Modal an"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/api/calendar-data", response_class=HTMLResponse)
async def get_calendar_data(request: Request):
    """Gibt die Daten für den Kalender zurück"""
    form_data = await request.form()
    # Lese compact_mode aus Query-Parametern
    compact_mode = request.query_params.get("compact", "0")

    # Definiere Höhen für normale und kompakte Ansicht
    base_row_height = 9  # normale Höhe
    compact_row_height = 5  # kompakte Höhe
    current_row_height = compact_row_height if compact_mode == "1" else base_row_height

    # Tage aller Planperioden, gruppieren nach Monat und plan_periods
    period_colors = {}
    grouped_dates = {} 
    period_deadlines = {}
    period_messages = {}  # Dictionary für die Mitteilungen
    period_first_month = {}  # Speichert den ersten Monat jeder Periode
    sorted_periods = []
    for period in plan_periods:
        text_plan_periods = f'{period["start"].strftime("%d.%m.%y")} - {period["end"].strftime("%d.%m.%y")}'
        period_deadlines[text_plan_periods] = period["deadline"]
        period_messages[text_plan_periods] = period["message"]
        
        # Ersten Monat für jede Periode speichern
        period_first_month[text_plan_periods] = period["start"].month
        
        for day in range((period['end'] - period['start']).days + 1):
            day_date = period['start'] + timedelta(days=day)
            if day_date.month not in grouped_dates:
                grouped_dates[day_date.month] = {
                    'year': day_date.year,
                    'periods': {}
                }
            if text_plan_periods not in grouped_dates[day_date.month]['periods']:
                grouped_dates[day_date.month]['periods'][text_plan_periods] = []
            grouped_dates[day_date.month]['periods'][text_plan_periods].append(day_date)

    # Sortierte Perioden basierend auf der Startdatum
    sorted_periods = sorted(list({period for periods in grouped_dates.values() 
                                for period in periods['periods'].keys()}), 
                                key=lambda x: (x.split(' - ')[0].split('.')[2], 
                                                x.split(' - ')[0].split('.')[1], 
                                                x.split(' - ')[0].split('.')[0]))

    # Generiere Farben für die Planungsperioden
    for month, month_periods in grouped_dates.items():
        for period in month_periods['periods'].keys():
            if period not in period_colors:
                period_colors.update({period: colors_for_periods[len(period_colors) % len(colors_for_periods)]})

    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "grouped_dates": grouped_dates,
        "period_deadlines": period_deadlines,
        "period_messages": period_messages,
        "period_first_month": period_first_month,  # Übergebe die Information über den ersten Monat
        "selected_times": selected_times,  # Füge selected_times zum Template Context hinzu
        "user_notes": user_notes,  # Füge user_notes zum Template Context hinzu
        "sorted_periods": sorted_periods,  # Neue Variable für das Template,
        "colors_times_of_day": colors_times_of_day,
        "period_translation": period_translation,
        "compact_mode": compact_mode,
        "base_row_height": current_row_height,  # Verwende die dynamische Höhe
        "month_names": month_names,
        "period_colors": period_colors
    })

@app.get("/api/calendar-content", response_class=HTMLResponse)
async def get_calendar_content(request: Request):
    """Gibt die Daten für den Kalenderinhalt zurück"""
    # Debug prints
    print("Request headers:", request.headers)
    print("Query params:", request.query_params)
    
    # Lese compact_mode aus Query-Parametern
    compact_mode = request.query_params.get("compact", "0")

    # Wenn der Request vom Button kommt (HX-Target enthält view-mode-button)
    if "view-mode-button" in request.headers.get("HX-Target", ""):
        return templates.TemplateResponse(
            "calendar_view_mode_button.html",
            {
                "request": request,
                "compact_mode": compact_mode
            }
        ).body.decode()

    # Definiere Höhen für normale und kompakte Ansicht
    base_row_height = 9  # normale Höhe
    compact_row_height = 5  # kompakte Höhe
    current_row_height = compact_row_height if compact_mode == "1" else base_row_height

    # Tage aller Planperioden, gruppieren nach Monat und plan_periods
    period_colors = {}
    grouped_dates = {} 
    period_deadlines = {}
    period_messages = {}  # Dictionary für die Mitteilungen
    period_first_month = {}  # Speichert den ersten Monat jeder Periode
    sorted_periods = []
    for period in plan_periods:
        text_plan_periods = f'{period["start"].strftime("%d.%m.%y")} - {period["end"].strftime("%d.%m.%y")}'
        period_deadlines[text_plan_periods] = period["deadline"]
        period_messages[text_plan_periods] = period["message"]
        
        # Ersten Monat für jede Periode speichern
        period_first_month[text_plan_periods] = period["start"].month
        
        for day in range((period['end'] - period['start']).days + 1):
            day_date = period['start'] + timedelta(days=day)
            if day_date.month not in grouped_dates:
                grouped_dates[day_date.month] = {
                    'year': day_date.year,
                    'periods': {}
                }
            if text_plan_periods not in grouped_dates[day_date.month]['periods']:
                grouped_dates[day_date.month]['periods'][text_plan_periods] = []
            grouped_dates[day_date.month]['periods'][text_plan_periods].append(day_date)

    # Sortierte Perioden basierend auf der Startdatum
    sorted_periods = sorted(list({period for periods in grouped_dates.values() 
                                for period in periods['periods'].keys()}), 
                                key=lambda x: (x.split(' - ')[0].split('.')[2], 
                                                x.split(' - ')[0].split('.')[1], 
                                                x.split(' - ')[0].split('.')[0]))

    # Generiere Farben für die Planungsperioden
    for month, month_periods in grouped_dates.items():
        for period in month_periods['periods'].keys():
            if period not in period_colors:
                period_colors.update({period: colors_for_periods[len(period_colors) % len(colors_for_periods)]})
    
    print("Template variables:", {
        "grouped_dates": grouped_dates,
        "period_first_month": period_first_month,
        "period_deadlines": period_deadlines,
        "sorted_periods": sorted_periods,
        "compact_mode": compact_mode,
        "base_row_height": current_row_height,
        "month_names": month_names,
        "period_colors": period_colors
    })

    return templates.TemplateResponse(
        "calendar_container.html",
        {
            "request": request,
            "grouped_dates": grouped_dates,
            "period_first_month": period_first_month,
            "period_deadlines": period_deadlines,
            "sorted_periods": sorted_periods,
            "colors_times_of_day": colors_times_of_day,
            "period_translation": period_translation,
            "selected_times": selected_times,
            "compact_mode": compact_mode,
            "base_row_height": current_row_height,
            "month_names": month_names,
            "period_colors": period_colors
        }
    )

@app.post("/api/login", name="login")
async def login(request: Request):
    """Authentifiziert den Benutzer"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    # Hier Ihre Authentifizierungslogik einfügen
    if username == "admin" and password == "p":  # Beispiel-Credentials
        # Bei erfolgreicher Anmeldung den Kalender zurückgeben
        return await get_calendar_data(request)
    else:
        # Bei fehlgeschlagener Anmeldung einen JSON-Fehler zurückgeben
        return JSONResponse(
            content={
                "error": True,
                "error_message": "Anmeldedaten sind nicht korrekt"
            },
            status_code=401
        )

@app.get("/reset-password", name="reset_password")
async def reset_password(request: Request):
    """Zeigt die Passwort-Reset-Seite an"""
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request}
    )

@app.post("/api/reset-password-request", name="reset_password_request")
async def reset_password_request(request: Request):
    """Verarbeitet die Anfrage zum Zurücksetzen des Passworts"""
    form = await request.form()
    email = form.get("email")
    
    # Hier später die E-Mail-Logik implementieren
    # Erfolgstemplate zurückgeben, das das Formular ersetzt
    return templates.TemplateResponse(
        "reset_password_success.html",
        {
            "request": request,
            "email": email
        }
    )

@app.post("/api/load-period-notes", name="load_period_notes")
async def load_period_notes(request: Request):
    form = await request.form()
    period = form.get("period")
    color = form.get("color")

    print(f"Loading notes for period: {period}")
    print(f"Color: {color}")
    
    # Daten aus get_calendar_data abrufen
    calendar_response = await get_calendar_data(request)
    period_deadlines = calendar_response.context["period_deadlines"]
    period_messages = calendar_response.context["period_messages"]
    user_notes = calendar_response.context["user_notes"]

    # Generiere die Daten wie in get_calendar_data
    for p in plan_periods:
        text_plan_periods = f'{p["start"].strftime("%d.%m.%y")} - {p["end"].strftime("%d.%m.%y")}'
        period_deadlines[text_plan_periods] = p["deadline"]
        period_messages[text_plan_periods] = p["message"]
    
    print(f"Available periods: {list(period_deadlines.keys())}")
    print(f"Deadline for period: {period_deadlines.get(period)}")
    print(f"Message for period: {period_messages.get(period)}")
    
    if period:
        return templates.TemplateResponse(
            "period_notes.html",
            {
                "request": request,
                "period": period,
                "deadline": period_deadlines.get(period),
                "message": period_messages.get(period),
                "notes": user_notes.get(period, ""),
                "color": color
            }
        )
        print(f"Response: {response.body.decode()}")
        return response
    return {"error": "Period not found"}

@app.post("/api/save-notes", name="save_notes")
async def save_notes(request: Request):
    try:
        form = await request.form()
        period = form.get("period")
        notes = form.get("notes")
        success = True
        
        # Validiere die Eingaben
        if not period:
            return templates.TemplateResponse(
                "notification_error.html",
                {
                    "request": request,
                    "message": "Ungültige Eingabe"
                }
            )
            
        # Speichere oder lösche die Anmerkung 
        if notes:
            user_notes[period] = notes
        else:
            if period in user_notes:
                del user_notes[period]
            success = False
                
        return templates.TemplateResponse("notification_notes.html", {
            "request": request,
            "period": period,
            "success": success
        })
    except Exception as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": f"Fehler beim Speichern: {str(e)}"
            }
        )

@app.post("/api/select-time", name="select_time")
async def select_time(request: Request):
    try:
        form = await request.form()
        date = form.get("date")
        period = form.get("period")
        compact_mode = form.get("compact_mode")
        
        if not date or not period:
            return templates.TemplateResponse(
                "notification_error.html",
                {
                    "request": request,
                    "message": "Datum oder Tageszeit fehlt"
                }
            )

        date_object = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Toggle selection status
        is_checked = False
        if date in selected_times and period in selected_times[date]:
            selected_times[date].remove(period)
        else:
            if date not in selected_times:
                selected_times[date] = set()
            selected_times[date].add(period)
            is_checked = True

        curr_icon_color = colors_times_of_day[period]['checked' if is_checked else 'unchecked']
        curr_notification_colors = {
            'background': notification_colors['background']['checked' if is_checked else 'unchecked'],
            'border': notification_colors['border']['checked' if is_checked else 'unchecked'],
            'text': notification_colors['text']['checked' if is_checked else 'unchecked']
        }
        
        return templates.TemplateResponse(
            "period_response.html",
            {
                "request": request,
                "date": date_object,
                "period": period,
                "period_translation": period_translation,
                "checked": is_checked,
                "curr_icon_color": curr_icon_color,
                "curr_notification_colors": curr_notification_colors,
                "compact_mode": compact_mode
            }
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": str(e)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": f"Ein unerwarteter Fehler ist aufgetreten: {e}"
            }
        )


@app.get("/get-calendar-menus", response_class=HTMLResponse)
async def get_calendar_menus(request: Request):
    # Sortierte Perioden basierend auf der Startdatum
    sorted_periods = sorted((period["start"], period["end"]) for period in plan_periods)
    sorted_periods = [f'{period[0].strftime("%d.%m.%y")} - {period[1].strftime("%d.%m.%y")}' for period in sorted_periods]
    
    return templates.TemplateResponse("menus_calendar.html", {
        "request": request,
        "sorted_periods": sorted_periods
    })


@app.exception_handler(500)
async def internal_server_error(request: Request, exc: Exception):
    print(f"Server Error: {exc}")  # Debug print
    if "hx-request" in request.headers:
        # HTMX Request - zeige Notification
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": f"Server Fehler: {str(exc)}"  # Zeige den tatsächlichen Fehler
            }
        )
    else:
        # Normaler Request - zeige Fehlerseite
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Ein unerwarteter Fehler ist aufgetreten: {str(exc)}"
            },
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)