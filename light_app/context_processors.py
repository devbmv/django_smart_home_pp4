from home_control_project.settings import home_online_status

def home_status_processor(request):
    user_id = request.user.id if request.user.is_authenticated else None
    return {
        'home_online_status': home_online_status.get(user_id, False) 
    }
