* ImageRepository 에서 AdminImageRepository 를 분리해 구현
    * admin 전용으로 검사 없이 동작할 메소드들
* ImageService 동작 중 ImageRepository 의 메소드를 한번만 호출해서 동작 가능한 경우들은 1회로 호출하게 수정
    * DB 접근을 분리해서 접근할 경우 성능 저하가 발생할 수 있음
* Repository에서 ImageRow 등의 row 객체를 반환하지 않고, ImageData 등의 dataclass 를 반환하도록 수정
    * Repository 에서만 row 객체를 사용하고, 서비스에서는 dataclass 를 사용하도록 변경
* services 의 하위 패키지에서만 사용되는 Exception이 repository에서 사용해야하는 상황이 있다면 errors/exception.py 패키지로 옮긴 후 repository 에서도 사용하도록 변경
