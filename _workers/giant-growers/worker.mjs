export default {
  fetch() {
    return new Response('이 게임의 공개 서비스가 종료되었습니다.', {
      status: 410,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  },
};
