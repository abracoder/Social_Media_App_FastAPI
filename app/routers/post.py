from fastapi import Response,status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from typing import List,Optional
from .. import models,schemas,oauth2
from ..database import get_db
from sqlalchemy import func


router=APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get("/",response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db),curr_user:int=Depends(oauth2.get_current_user),limit:int=10,skip:int=0,search:Optional[str]=""):
    # cursor.execute("""SELECT * FROM posts""")
    # posts=cursor.fetchall()
    # print("user id",curr_user.email)

    posts=db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    results=db.query(models.Post,func.count(models.Vote.post_id).label("votes")).join(models.Vote,models.Vote.post_id==models.Post.id,isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    # print(results)
    return results



@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.Post)
def create_posts(post:schemas.PostCreate,db: Session = Depends(get_db),curr_user:int=Depends(oauth2.get_current_user)):
    # cursor.execute("""INSERT INTO posts (title,content,published) VALUES(%s,%s,%s) RETURNING *""",(post.title,
    # post.content,post.published))
    # new_post=cursor.fetchone()
    # conn.commit()
    # post.dict
    # print("user id",curr_user.email)
    
    new_post=models.Post(owner_id=curr_user.id,**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)   
    return new_post


@router.get("/{id}",response_model=schemas.PostOut)
def get_post(id:int,response:Response,db: Session = Depends(get_db),curr_user:int=Depends(oauth2.get_current_user)):
    # id_list=[id]
    # cursor.execute("""SELECT * from posts WHERE id = %s""",(id,))
    # fetched_post=cursor.fetchone()
    fetched_post=db.query(models.Post,func.count(models.Vote.post_id).label("votes")).join(models.Vote,models.Vote.post_id==id,isouter=True).group_by(models.Post.id).first()
    if not fetched_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {id}  was not found")
    return fetched_post


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id:int,db: Session = Depends(get_db),curr_user:int=Depends(oauth2.get_current_user)):
    
    # cursor.execute("""DELETE FROM posts where id =%s returning *""",(id,))
    # deleted_post=cursor.fetchone()
    post_query=db.query(models.Post).filter(models.Post.id==id)
    post=post_query.first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {id} doesn't exist")
    # conn.commit()
    if post.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}",response_model=schemas.Post)
def update_post(id:int,post:schemas.PostUpdate,db: Session = Depends(get_db),curr_user:int=Depends(oauth2.get_current_user)):
    # cursor.execute("""UPDATE posts SET title=%s,content=%s,published=%s WHERE id =%s RETURNING *""",(post.title,post.content,post.published,id,))
    # updated_post=cursor.fetchone()
    post_query=db.query(models.Post).filter(models.Post.id==id)
    updated_post=post_query.first()
    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {id} doesn't exist")
    # conn.commit()
    if updated_post.owner_id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorized to perform requested action")
    
    post_query.update(post.dict(),synchronize_session=False)
    db.commit()
    return post_query.first()