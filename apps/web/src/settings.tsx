import React,{useEffect,useState} from 'react';
import {api} from './api';
import type {Me,Project} from './types';

export function ProjectSettings({project,onSave}:{project:Project;onSave:(p:Project)=>void}) {
 const [templates,setTemplates]=useState<{id:string;name:string;official_flag:boolean}[]>([]);
 const [message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{void api<typeof templates>('/templates').then(setTemplates).catch(e=>setMessage(e.message));},[]);
 return <details className="panel"><summary>프로젝트 설정</summary><form key={project.id+project.name+project.security_class+project.template_id} className="new-project" onSubmit={async e=>{
   e.preventDefault();const data=new FormData(e.currentTarget);setBusy(true);setMessage('');
   try{onSave(await api<Project>(`/projects/${project.id}`,{method:'PATCH',body:JSON.stringify({name:data.get('name'),description:data.get('description'),security_class:data.get('security_class'),template_id:data.get('template_id')||null})}));setMessage('프로젝트 설정을 저장했습니다.');}
   catch(e){setMessage((e as Error).message);}finally{setBusy(false);}
 }}>
  <label>프로젝트 이름<input name="name" aria-label="프로젝트 설정 이름" defaultValue={project.name} maxLength={120} required/></label>
  <label>설명<input name="description" aria-label="프로젝트 설정 설명" defaultValue={project.description} maxLength={2000}/></label>
  <label>보안등급<input name="security_class" aria-label="프로젝트 보안등급" defaultValue={project.security_class} maxLength={30} required/></label>
  <label>기본 PPT 템플릿<select name="template_id" aria-label="기본 PPT 템플릿" defaultValue={project.template_id??''}><option value="">기본 개발 템플릿</option>{templates.map(t=><option key={t.id} value={t.id}>{t.name}{t.official_flag?'':' (개발용)'}</option>)}</select></label>
  <p className="hint">소속 조직은 생성자의 조직으로 지정됩니다. 기관 보안등급과 공식 템플릿은 확정 후 설정합니다.</p>
  <button disabled={busy}>프로젝트 설정 저장</button>{message&&<p role="status">{message}</p>}
 </form></details>;
}

interface ManagedUser {id:string;username:string;role:string;active:boolean}
export function UserAdmin({me}:{me:Me}) {
 const [users,setUsers]=useState<ManagedUser[]>([]),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{void api<ManagedUser[]>('/admin/users').then(setUsers).catch(e=>setMessage(e.message));},[]);
 async function save(user:ManagedUser){setBusy(true);try{const updated=await api<ManagedUser>(`/admin/users/${user.id}`,{method:'PATCH',body:JSON.stringify({role:user.role,active:user.active})});setUsers(old=>old.map(u=>u.id===updated.id?updated:u));setMessage(`${user.username} 권한과 활성 상태를 저장했습니다.`);}catch(e){setMessage((e as Error).message);}finally{setBusy(false);}}
 return <section className="panel"><h2>사용자 관리</h2><p>접근 가능한 조직의 계정입니다. 변경 전후 상태는 감사로그에 기록됩니다.</p>{message&&<p role="status">{message}</p>}
 {users.map(u=><div className="artifact-row" key={u.id}><strong>{u.username}</strong><select aria-label={`${u.username} 역할`} value={u.role} disabled={busy||(me.role!=='SystemAdmin'&&u.role==='SystemAdmin')} onChange={e=>setUsers(old=>old.map(v=>v.id===u.id?{...v,role:e.target.value}:v))}>{['User','Reviewer','OrgAdmin','SystemAdmin'].filter(r=>me.role==='SystemAdmin'||r!=='SystemAdmin'||u.role==='SystemAdmin').map(r=><option key={r}>{r}</option>)}</select><label><input type="checkbox" checked={u.active} onChange={e=>setUsers(old=>old.map(v=>v.id===u.id?{...v,active:e.target.checked}:v))}/>활성</label><button disabled={busy||(me.role!=='SystemAdmin'&&u.role==='SystemAdmin')} onClick={()=>void save(u)}>저장</button></div>)}
 </section>;
}
