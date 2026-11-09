"""Safe Talos-derived reactions. No serial connection is ever opened here."""


def sensor_context(present: bool) -> dict:
    if type(present) is not bool:
        raise ValueError('present must be a boolean')
    return {'present': present, 'sensor': 'PIR',
            'learning_mode': 'guided' if present else 'paused',
            'ai_context': 'Ofereça uma dica curta.' if present else 'Aguarde o retorno do participante.'}


def react(correct: bool, present: bool = True) -> dict:
    if type(correct) is not bool or type(present) is not bool:
        raise ValueError('correct and present must be booleans')
    action = ('arm_wave' if correct else 'head_wave') if present else 'stop'
    return {'simulated': True, 'action': action, 'status': 'simulated',
            'face': ('happy' if correct else 'encouraging') if present else 'idle',
            'motor': (2 if correct else 1) if present else None,
            'context': sensor_context(present),
            'physical_verified': False}


class Gateway:
    """Simulator boundary: hardware enablement requires a separately reviewed adapter."""
    def __init__(self, mode='simulate'):
        if mode != 'simulate':
            raise ValueError('Hardware mode unavailable until wiring and emergency stop are verified')

    def react(self, correct: bool, present: bool = True) -> dict:
        return react(correct, present)
