from app.data import media
from sqlalchemy.orm import Session, load_only
from sqlalchemy.orm.attributes import flag_modified
from typing import List
from random import sample
from datetime import datetime
from app.data import models, schemas
from app.auth.hash import hash
import geopy.distance

def get_user_by_email(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first()

def get_hashed(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().hashed

def get_auth_profile(db: Session, id: int):
    return db.query(models.Auth).filter(models.Auth.user_id == id).first()

def get_id(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().user_id

def get_profile(db: Session, id: int):
    profile = db.query(models.Profile).options(load_only(models.Profile.name, models.Profile.status, models.Profile.about, models.Profile.age, models.Profile.avatar, models.Profile.preferences)).get(id).__dict__
    if profile['avatar']:
        profile['avatar'] = media.get_avatar(id)
    else:
        profile['avatar'] = None
    return profile

def get_profile_name(db: Session, id: int):
    return db.query(models.Profile).filter(models.Profile.id == id).first().name

def get_fcm_token(db: Session, id: int):
    return db.query(models.Profile).filter(models.Profile.id == id).first().fcm_token

def write_message(db: Session, sender: int, recipient: int, text: str = None):
    message = models.Messages(sender=sender, recipient=recipient, message=text)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def add_files_to_message(db: Session, id: int, filenames: list[str]):
    message = db.query(models.Messages).get(id)
    message.attachments = filenames
    flag_modified(message, 'attachments')
    db.merge(message)
    db.flush()
    db.commit()

def get_messages(db: Session, sender: int, recipient: int):
    messages = db.query(models.Messages).filter(models.Messages.sender == sender, models.Messages.recipient == recipient).all() + db.query(models.Messages).filter(models.Messages.sender == recipient, models.Messages.recipient == sender).all()
    result = []
    for message in messages:
        message_dict = message.__dict__
        if message_dict['attachments']:
            message_dict['attachments'] = media.get_chat(message_dict['attachments'])
        else:
            message_dict['attachments'] = None
        result.append(message_dict)
    return result

def get_all_messages(db: Session, id: int):
    messages = db.query(models.Messages).filter(models.Messages.sender == id).all() + db.query(models.Messages).filter(models.Messages.recipient == id).all()
    result = []
    added = []
    for message in messages:
        if message.recipient != id and message.recipient not in added:
            result.append([message.recipient, db.query(models.Messages).filter(models.Messages.recipient == message.recipient, models.Messages.sender == id).all() + db.query(models.Messages).filter(models.Messages.recipient == id, models.Messages.sender == message.recipient).all()])
            added.append(message.recipient)
        elif message.sender != id and message.sender not in added:
            result.append([message.sender, db.query(models.Messages).filter(models.Messages.recipient == message.sender, models.Messages.sender == id).all() + db.query(models.Messages).filter(models.Messages.recipient == id, models.Messages.sender == message.sender).all()])
            added.append(message.sender)
    for i in range(len(result)):
        result[i][0] = db.query(models.Profile).get(result[i][0]).name
        for j in range(len(result[i][1])):
            result[i][1][j] = result[i][1][j].__dict__
            result[i][1][j]["sender"] = db.query(models.Profile).get(result[i][1][j]["sender"]).name
            result[i][1][j]["recipient"] = db.query(models.Profile).get(result[i][1][j]["recipient"]).name
            if result[i][1][j]["attachments"] == []:
                result[i][1][j]["attachments"] = None
            else:
                result[i][1][j]["attachments"] = ' '.join(result[i][1][j]["attachments"])
    return result
def get_images(db: Session, id: int):
    return db.query(models.Profile).filter(models.Profile.id == id).first().images

def add_image(db: Session, id: int):
    profile = db.query(models.Profile).get(id)
    profile.images.append(str(id) + '_' + str(profile.uploaded) + '.png')
    profile.uploaded += 1
    flag_modified(profile, 'images')
    db.merge(profile)
    db.flush()
    db.commit()
    return profile.uploaded - 1

def delete_image(db: Session, id: int, file: str):
    profile = db.query(models.Profile).get(id)
    profile.images.remove(file)
    flag_modified(profile, 'images')
    db.merge(profile)
    db.flush()
    db.commit()

def create_avatar(db: Session, id: int):
    profile = db.query(models.Profile).get(id)
    profile.avatar = True
    db.commit()

def get_full_profile(db: Session, id: int):
    return db.query(models.Profile).get(id)

def create_profile(db: Session, profile: schemas.ProfileCreate) -> models.Profile:
    db_profile = models.Profile(name=profile.name, birth=profile.birth, sex=profile.sex, fcm_token=profile.fcm_token)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def create_auth(db: Session, auth: schemas.AuthCreate, profile: schemas, id: str) -> models.Auth:
    db_auth = models.Auth(email=auth.email, hashed=hash(auth.password), user_id=profile.id, id=id, sent=datetime.today())
    db.add(db_auth)
    db.commit()
    db.refresh(db_auth)
    return db_auth

def change_auth_id(db: Session, email: str, id: str):
    old_id = db.query(models.Auth).filter(models.Auth.email == email).first().id
    db_auth = db.query(models.Auth).get(old_id)
    db_auth.id = id
    db.commit()

def change_auth_sent(db: Session, email: str, sent: datetime):
    old_id = db.query(models.Auth).filter(models.Auth.email == email).first().id
    db_auth = db.query(models.Auth).get(old_id)
    db_auth.sent = sent
    db.commit()

def change_name(db: Session, id: int, name: str):
    profile = db.query(models.Profile).get(id)
    profile.name = name
    db.commit()

def change_about(db: Session, id: int, about: str):
    profile = db.query(models.Profile).get(id)
    profile.about = about
    db.commit()

def change_status(db: Session, id: int, status: str):
    profile = db.query(models.Profile).get(id)
    profile.status = status
    db.commit()

def set_cords(db: Session, id: int, latitude: float, longitude: float):
    profile = db.query(models.Profile).get(id)
    profile.latitude = latitude
    profile.longitude = longitude
    db.commit()

def like(db: Session, initiator: id, target: id):
    db_like = models.Like(initiator=initiator, target=target)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like

def match(db: Session, initiator: id, target: id):
    db_like = db.query(models.Like).filter(models.Like.initiator == initiator, models.Like.target == target).first()
    db_like.match = True
    db.commit()

def get_like(db: Session, initiator: id, target: id):
    return db.query(models.Like).filter(models.Like.initiator == initiator, models.Like.target == target).first()

def get_dislike(db: Session, initiator: int, target: int):
    return db.query(models.Dislike).filter(models.Dislike.initiator == initiator, models.Dislike.target == target).first()

def dislike(db: Session, initiator: id, target: id):
    db_dislike = models.Dislike(initiator=initiator, target=target)
    db.add(db_dislike)
    db.commit()
    db.refresh(db_dislike)
    return db_dislike
    
def delete_like(db: Session, initiator: int, target: int):
    like = db.query(models.Like).filter(models.Like.initiator == initiator, models.Like.target == target).first()
    db.delete(like)
    db.commit()

def delete_dislike(db: Session, initiator: int, target: int):
    dislike = db.query(models.Dislike).filter(models.Dislike.initiator == initiator, models.Dislike.target == target).first()
    db.delete(dislike)
    db.commit()

def get_all_profiles(db: Session, id: int, agefrom: int, ageto: int) -> List[models.Profile]:
    user = db.query(models.Profile).get(id)
    profiles = db.query(models.Profile).filter(models.Profile.id != id, models.Profile.age >= agefrom, models.Profile.age <= ageto).options(load_only(models.Profile.name, models.Profile.status, models.Profile.age, models.Profile.avatar, models.Profile.latitude, models.Profile.longitude)).all()
    result = []
    for profile in profiles:
        profile_dict = profile.__dict__
        if profile_dict['avatar']:
            profile_dict['avatar'] = media.get_avatar(id)
        else:
            profile_dict['avatar'] = None
        if profile_dict['longitude'] and profile_dict['latitude'] and user.latitude and user.longitude:
            profile_dict['distance'] = geopy.distance.geodesic((profile_dict['latitude'], profile_dict['longitude']), (user.latitude, user.longitude)).km
        del profile_dict['longitude']
        del profile_dict['latitude']
        result.append(profile_dict)
    return result

def get_all_profiles_by_sex(db: Session, id: int, agefrom: int, ageto: int, sex: str) -> List[models.Profile]:
    user = db.query(models.Profile).get(id)
    profiles = db.query(models.Profile).filter(models.Profile.id != id, models.Profile.age >= agefrom, models.Profile.age <= ageto, models.Profile.sex == sex).options(load_only(models.Profile.name, models.Profile.status, models.Profile.age, models.Profile.avatar, models.Profile.latitide, models.Profile.longitude)).all()
    result = []
    for profile in profiles:
        profile_dict = profile.__dict__
        if profile_dict['avatar']:
            profile_dict['avatar'] = media.get_avatar(id)
        else:
            profile_dict['avatar'] = None
        if profile_dict['longitude'] and profile_dict['latitude'] and user.latitude and user.longitude:
            geopy.distance.geodesic((profile_dict['latitude'], profile_dict['longitude']), (user.latitude, user.longitude)).km
            del profile_dict['longitude']
            del profile_dict['latitude']
        result.append(profile_dict)
    return result

def verify_auth(db: Session, id: str):
    db_auth = db.query(models.Auth).get(id)
    db_auth.verified = True
    db.commit()

def delete_user(db: Session, id: int):
    profile = db.query(models.Profile).filter(models.Profile.id == id).first()
    auth = db.query(models.Auth).filter(models.Auth.user_id == id).first()
    likes_initiator = db.query(models.Like).filter(models.Like.initiator == id).all()
    likes_target = db.query(models.Like).filter(models.Like.target == id).all()
    dislikes = db.query(models.Dislike).filter(models.Dislike.initiator == id).all()
    db.delete(profile)
    db.delete(auth)
    for item in likes_initiator:
        db.delete(item)
    for item in likes_target:
        db.delete(item)
    for item in dislikes:
        db.delete(item)
    db.commit()

def get_verified(db: Session, id: str):
    return db.query(models.Auth).filter(models.Auth.id == id).first().verified

def get_email_verified(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().verified

def get_auth(db: Session, id: str):
    return db.query(models.Auth).filter(models.Auth.id == id).first()

def get_email_sent(db: Session, email: str):
    return db.query(models.Auth).filter(models.Auth.email == email).first().sent

def update_avatar(db: Session, id: int, url: str):
    profile = db.query(models.Profile).get(id)
    profile.avatar = url
    db.commit()

def get_likes(db: Session, id: int):
    result = []
    for like in db.query(models.Like).filter(models.Like.target == id).options(load_only(models.Like.initiator, models.Like.match)).all():
        like_dict = like.__dict__
        del like_dict["id"]
        result.append(like_dict)
    return result

def get_all_likes_name_users(db: Session, id: int):
    initiator =  db.query(models.Like).filter(models.Like.initiator == id).options(load_only(models.Like.target)).all()
    target = db.query(models.Like).filter(models.Like.target == id, models.Like.match == True).options(load_only(models.Like.initiator)).all()
    result = []
    for likeObject in initiator:
        result.append((db.query(models.Profile).get(likeObject.target).name, likeObject.created))
    for likeObject in target:
        result.append((db.query(models.Profile).get(likeObject.initiator).name, likeObject.created))
    return result

def get_all_dislikes_name_users(db: Session, id: int):
    initiator =  db.query(models.Dislike).filter(models.Dislike.initiator == id).options(load_only(models.Dislike.target)).all()
    result = []
    for dislikeObject in initiator:
        result.append((db.query(models.Profile).get(dislikeObject.target).name, dislikeObject.created))
    return result