let accessToken = '';
export function setToken(value: string) { accessToken = value; }
export function getToken() { return accessToken; }
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  let result = await fetch('/api/v1' + path, {...init, headers, credentials:'same-origin'});
  if (result.status === 401 && accessToken && !path.startsWith('/auth')) {
    const refresh = await fetch('/api/v1/auth/refresh', {method:'POST',credentials:'same-origin'});
    if (refresh.ok) { accessToken = (await refresh.json()).access_token; headers.set('Authorization',`Bearer ${accessToken}`); result = await fetch('/api/v1'+path,{...init,headers}); }
  }
  if (!result.ok) { const data = await result.json(); throw new Error(data.error?.code ?? `HTTP_${result.status}`); }
  if (result.status === 204) return undefined as T;
  return result.json() as Promise<T>;
}
export const post = <T>(path:string, data: unknown = {}) => api<T>(path,{method:'POST',body:JSON.stringify(data)});
export async function download(id:string, version?:string) {
  const result = await fetch(`/api/v1/artifacts/${id}/download${version ? '?version_id='+version : ''}`,{headers:{Authorization:`Bearer ${accessToken}`}});
  if (!result.ok) throw new Error('다운로드 권한 또는 세션을 확인하세요.');
  return {blob:await result.blob(),name:result.headers.get('content-disposition')?.match(/filename="?([^";]+)/)?.[1] ?? 'artifact'};
}
export const stateLabel:Record<string,string> = {QUEUED:'대기 중',RUNNING:'실행 중',WAITING_REVIEW:'계획 검토 필요',SUCCEEDED:'작업 완료',FAILED:'실패',CANCELLED:'취소됨',RETRYING:'재시도 중',APPROVED:'승인됨',DRAFT:'초안',VALIDATED:'검증됨',REVIEWED:'검토됨'};
export const canGenerate = (status:string, version:number, approved:number|null) => status === 'APPROVED' && version === approved;
