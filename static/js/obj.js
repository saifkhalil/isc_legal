$(document).ready(function () {
           $(".select2").each(function () {
                      $(this).select2({
                          theme: "bootstrap-5",
                          width: "100%",
                      });
                  });
            $("#id_case_type").change(function () {
                var caseTypeID = $(this).val();
                var stageField = $("#id_Stage");

                if (caseTypeID) {
                    $.ajax({
                        url: "{% url 'get_stages' %}",
                        data: { case_type_id: caseTypeID },
                        dataType: "json",
                        success: function (data) {
                            stageField.empty();  // Clear previous options

                            if (data.stages.length > 0) {
                                stageField.prop("disabled", false);
                                $.each(data.stages, function (index, stage) {
                                    stageField.append($('<option>', {
                                        value: stage.id,
                                        text: stage.name
                                    }));
                                });
                            } else {
                                stageField.prop("disabled", true); // Disable if no stages found
                            }
                        }
                    });
                } else {
                    stageField.prop("disabled", true);
                    stageField.empty();
                }
            });
        });