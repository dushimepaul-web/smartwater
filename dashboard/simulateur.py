import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings

SCENARIOS = {
    'normal': 'Normal',
    'vidange': 'Vidange',
    'remplissage': 'Remplissage',
}

ETAT = Path(tempfile.gettempdir()) / 'smartwater_simulation.json'
VERROU = Path(tempfile.gettempdir()) / 'smartwater_simulation.lock'
JOURNAL = Path(tempfile.gettempdir()) / 'smartwater_simulation.log'


@contextmanager
def _verrou():
    import fcntl
    with open(VERROU, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _pid_actif(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    return True


def etat_simulation():
    try:
        data = json.loads(ETAT.read_text())
    except (FileNotFoundError, ValueError):
        return None
    if not _pid_actif(data.get('pid')):
        try:
            ETAT.unlink()
        except FileNotFoundError:
            pass
        return None
    return data


def simulation_active():
    etat = etat_simulation()
    return etat['scenario'] if etat else None


def _arreter_etat(etat):
    pid = etat.get('pid')
    if _pid_actif(pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
        for _ in range(20):
            if not _pid_actif(pid):
                break
            time.sleep(0.1)
        if _pid_actif(pid):
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass
    try:
        ETAT.unlink()
    except FileNotFoundError:
        pass


def arreter_simulation():
    with _verrou():
        etat = etat_simulation()
        if etat:
            _arreter_etat(etat)


def demarrer_simulation(scenario, capteur_id):
    if scenario not in SCENARIOS:
        return False, 'Scénario inconnu.'
    if not capteur_id:
        return False, 'Aucun capteur disponible.'
    with _verrou():
        etat = etat_simulation()
        if etat:
            _arreter_etat(etat)
        commande = [
            sys.executable,
            str(settings.BASE_DIR / 'manage.py'),
            'simuler_capteur',
            '--capteur', str(capteur_id),
            '--scenario', scenario,
            '--intervalle', '2',
        ]
        with open(JOURNAL, 'ab') as journal:
            processus = subprocess.Popen(
                commande,
                cwd=str(settings.BASE_DIR),
                stdout=journal,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=os.environ.copy(),
            )
        time.sleep(0.8)
        if processus.poll() is not None:
            try:
                lignes = JOURNAL.read_text(errors='replace').splitlines()[-5:]
            except FileNotFoundError:
                lignes = []
            return False, ' '.join(lignes) or 'Le simulateur s’est arrêté immédiatement.'
        ETAT.write_text(json.dumps({
            'scenario': scenario,
            'pid': processus.pid,
            'capteur': int(capteur_id),
        }))
        return True, ''
