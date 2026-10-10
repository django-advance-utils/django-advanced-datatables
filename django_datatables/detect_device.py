def detect_device(request):
    # A request need not send a User-Agent (curl, monitoring checks, some
    # bots), so a missing one counts as not mobile rather than raising.
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return {'mobile': 'android' in user_agent or 'iphone' in user_agent}
