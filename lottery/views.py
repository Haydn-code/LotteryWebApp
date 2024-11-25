# IMPORTS
from flask import Blueprint, render_template, request, flash
from sqlalchemy.orm import make_transient
from app import db, roles_required
from models import Draw
from flask_login import current_user, login_required

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@roles_required('user')
def lottery():
    return render_template('lottery/lottery.html')


@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
@roles_required('user')
def add_draw():
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    submitted_draw.strip()

    # create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, numbers=submitted_draw, master_draw=False, lottery_round=0,
                    drawkey=current_user.drawkey)  # TODO: update user_id [user_id=1 is a placeholder]

    # add the new draw to the database
    db.session.add(new_draw)
    db.session.commit()

    # re-render lottery.page
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@roles_required('user')
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(been_played=False, user_id=current_user.id).all()  # TODO: filter playable draws for current user
    # iterates through all playable draws and gets corresponding encryption key to decrypt draws for user to see
    for draws in playable_draws:
        make_transient(draws)
        draws.view_draw(current_user.drawkey)

    # if playable draws exist
    if len(playable_draws) != 0:
        # re-render lottery page with playable draws
        return render_template('lottery/lottery.html', playable_draws=playable_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
@roles_required('user')
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(been_played=True, user_id=current_user.id).all()  # TODO: filter played draws for current user

    # if played draws exist
    if len(played_draws) != 0:
        return render_template('lottery/lottery.html', results=played_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
@roles_required('user')
def play_again():
    Draw.query.filter_by(been_played=True, master_draw=False, user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()


