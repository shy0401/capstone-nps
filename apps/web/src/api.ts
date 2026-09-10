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
  if (!result.ok) { const data = await result.json().catch(()=>({})); const code=data.error?.code ?? `HTTP_${result.status}`; throw new Error(errorMessage(code)); }
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
export const canGenerate = (status:string, version:number, approved:number|null, prototypePass=false) => prototypePass || (status === 'APPROVED' && version === approved);

export function errorMessage(code:string):string { const messages:Record<string,string>={PLAN_REVIEW_REQUIRED:'계획 승인이 필요합니다. 검토패스 모드 적용 여부를 확인하세요.',PPT_REVIEW_REQUIRED:'먼저 PPTX를 검토한 뒤 영상을 생성하세요.',HWP_DISTRIBUTION_UNSUPPORTED:'배포용 HWP는 현재 지원하지 않습니다. 권한이 있는 원본을 HWPX 또는 PDF로 저장해 업로드하세요.',VIDEO_CONTENT_OVERFLOW:'영상 한 장면에 내용이 너무 많습니다. 슬라이드 본문을 나누거나 줄여 저장한 뒤 재시도하세요.',DOC_NOT_CLEAN:'문서 보안검사가 완료된 뒤 분석할 수 있습니다.'};return messages[code]?`${messages[code]} (${code})`:code;}
