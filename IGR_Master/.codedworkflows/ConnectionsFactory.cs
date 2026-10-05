using UiPath.CodedWorkflows;
using System;

namespace IGR_Master
{
    public class GoogleDocsFactory
    {
        public GoogleDocsFactory(ICodedWorkflowsServiceContainer resolver)
        {
        }
    }

    public class DriveFactory
    {
        public UiPath.GSuite.Activities.Api.DriveConnection UnAttended_raservicespune_gmail_com { get; set; }
        public UiPath.GSuite.Activities.Api.DriveConnection UnAttended_GoogleDrive_Prod { get; set; }

        public DriveFactory(ICodedWorkflowsServiceContainer resolver)
        {
            UnAttended_raservicespune_gmail_com = new UiPath.GSuite.Activities.Api.DriveConnection("07d2357f-01e7-423f-b76d-b0c7b72314dd", resolver);
            UnAttended_GoogleDrive_Prod = new UiPath.GSuite.Activities.Api.DriveConnection("f70f909c-8a3f-4340-934a-764aaaff77f5", resolver);
        }
    }

    public class GoogleFormsFactory
    {
        public GoogleFormsFactory(ICodedWorkflowsServiceContainer resolver)
        {
        }
    }

    public class GmailFactory
    {
        public UiPath.GSuite.Activities.Api.GmailConnection UnAttended_raservicespune_gmail_com { get; set; }

        public GmailFactory(ICodedWorkflowsServiceContainer resolver)
        {
            UnAttended_raservicespune_gmail_com = new UiPath.GSuite.Activities.Api.GmailConnection("8c6e332c-054b-4d91-acdf-550e7c2d278e", resolver);
        }
    }

    public class GoogleSheetsFactory
    {
        public GoogleSheetsFactory(ICodedWorkflowsServiceContainer resolver)
        {
        }
    }

    public class GoogleTasksFactory
    {
        public GoogleTasksFactory(ICodedWorkflowsServiceContainer resolver)
        {
        }
    }

    public class GoogleWorkspaceFactory
    {
        public GoogleWorkspaceFactory(ICodedWorkflowsServiceContainer resolver)
        {
        }
    }
}