var OriginTitle = document.title;
var titleTime;
document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
        $('[rel="icon"]').attr('href', "http://www.12cow.com/wp-content/uploads/2020/02/cropped-%E5%A4%B4%E5%83%8F.jpg");
        document.title = '你不要我了吗';
        clearTimeout(titleTime);
    }
    else {
        $('[rel="icon"]').attr('href', "http://www.12cow.com/wp-content/uploads/2020/02/cropped-%E5%A4%B4%E5%83%8F.jpg");
        document.title = 我喜欢你！' + OriginTitle;
        titleTime = setTimeout(function () {
            document.title = OriginTitle;
        }, 2000);
    }
});