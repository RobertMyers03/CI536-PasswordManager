module com.example.passwordmanager {
    requires javafx.controls;
    requires javafx.fxml;


    opens com.example.passwordmanager to javafx.fxml;
    exports com.example.passwordmanager;
}